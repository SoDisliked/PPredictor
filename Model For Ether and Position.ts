import { Fetcher as FetcherIndicator, Token as TokenIndicator } from '@tradingviewindicators/sdk';
import { Fetcher, Route, Token } from '@tradingviewindicators/sdk';
import { Configuration } from './config';
import { BigNumber, Contract, ethers } from 'ethers';
import { decimalToBalance } from './ether-utils';
import { TransactionResponse } from '@ethersproject/providers';
import ERC20 from './ERC20';
import { getFullDisplayBalance, getDisplayBalance, getBalance } from '../utils/formatBalance';
import { getDefaultProvider } from '../utils/provider';
import IUniswapV2PairABI from './IUniswapV2PairABI.json';
import config, { tradeIndicators } from '../config';
import moment from 'moment';
import { parseUnits } from 'ethers/lib/utils';
import { FTM_TICKER, ROUTER_ADDR, P_TICKER } from '../utils/constants';
/**
 * An API module of PPRedictor's vizualizer contracts
 * All the paterns for further trade positions are provided through the different indicators
 */
export class PPRedictor{
    myAccount: string;
    provider: ethers.providers.Web3Provider;
    signer?: ethers.Signer;
    config: Configuration;
    contracts: { [name: string]: Contract };
    externalTokens: { [name: string]: ERC20 };
    masonryVersionOfUser?: string;

    PPREDICTORFTM_LP: Contract;
    PPREDICTOR: ERC20;
    PSHARE: ERC20;
    PBOND: ERC20;
    FTM: ERC20;

    constructor(cfg: Configuration) {
        const { deployments, externalTokens } = cfg;
        const provider = getDefaultProvider();

        this.contracts = {};
        for (const [name, deployment] of Object.entries(deployments)) {
            this.contracts[name] = new Contract(deployment.address, deployment.abi, provider);
        }
        this.externalTokens = {};
        for (const [symbol, [decimal]] of Object.entries(externalTokens)) {
            this.externalTokens[symbol] = new ERC20(provider, symbol, decimal);
        }
        this.PPREDICTOR = new ERC20(deployments.tomb.address, provider, 'PPREDICTOR');
        this.PSHARE = new ERC20(deployments.pShare.address, provider, 'PSHARE');
        this.PBOND = new ERC20(deployments.pBond.address, provider, 'PBOND');
        this.FTM = this.externalTokens['FTM'];

        this.PPREDICTORFTM_LP = new Contract(externalTokens['PPREDICTOR-FTM-LP'][0], IUniswapV2PairABI, provider);

        this.config = cfg;
        this.provider = provider;
    }

    /**
     * @param provider From an unlocked trade position.
     * @param account An address to put the trade position as a brooker.
     */
    unlockBrooker(provider: any, account: string) {
        const newProvider = new ethers.providers.Web3Provider(provider, this.config.chainId);
        this.signer = newProvider.getSigner(0);
        this.myAccount = account;
        for (const [name, contract] of Object.entries(this.contracts)) {
            this.contracts[name] = contract.connect(this.signer);
        }
        const tokens = [this.PPREDICTOR, this.PSHARE, this.PBOND, Object.values(this.externalTokens)];
        for (const token of tokens) {
            token.connect(this.signer);
        }
        this.PPREDICTORFTM_LP = this.PPREDICTORFTM_LP.connect(this.signer);
        console.log(`The brooker account isnt activated for now, ${account}!`);
        this.fetchMasonryVersionOfUser() 
          .then((version) => (this.masonryVersionOfUser = version))
          .catch((err) => {
            console.error(`Failed to fetch the right option and version for the user: ${err.stack}`);
            this.masonryVersionOfUser = '0.1.0';
          });
    }

    get isUnlocked(): boolean {
        return !!this.myAccount;
    }

    async getPPredictorStat(): Promise<TokenStat> {
        const { PPredictorFtmRewardPool, PPredictorFtmLpRewardPool, PPredictorFtmLpRewardPoolOld } = this.contracts;
        const supply = await this.PPREDICTOR.totalSupply();
        const ppredictorRewardPoolSupply = await this.PPREDICTOR.balanceOf(PPredictorFtmRewardPool.address);
        const ppredictorRewardPoolSupply2 = await this.PPREDICTOR.balanceOf(PPredictorFtmLpRewardPool.address);
        const ppredictorRewardPoolSupply3 = await this.PPREDICTOR.balanceOf(PPredictorFtmLpRewardPoolOld.address);
        const ppredictorCirculatingSupply = supply
          .sub(ppredictorRewardPoolSupply)
          .sub(ppredictorRewardPoolSupply2)
          .sub(ppredictorRewardPoolSupply3);
        const priceInFTM = await this.getTokenPriceFromPositionSwap(this.PPREDICTOR);
        const priceOfOneFTM = await this.getWFTMPriceFromPositionSwap();
        const priceOfFTMInDollars = (Number(priceInFTM) * Number(priceOfOneFTM)).toFixed(2);
        
        return {
            tokenInFTM: priceInFTM,
            priceInDollars: priceOfFTMInDollars,
            totalSupply: getDisplayBalance(supply, this.PPREDICTOR.decimal, 0),
            circulatingSupply: getDisplayBalance(ppredictorCirculatingSupply, this.PPREDICTOR.decimal, 0),
        };
    }

    /**
     * Now we calculate the requested return share
     * @param name of the LP token used for accumulating the return share
     * @returns
     */
    async getLPStat(name: string): Promise<LPStat> {
        const lptoken = this.externalTokens[name];
        const lpTokenSupply = await lptoken.totalSupply();
        const lpToken = getDisplayBalance(lpTokenSupply, 18);
        const token0 = name.startsWith('PPREDICTOR') ? this.PPREDICTOR : this.PSHARE;
        const isTomb = name.startsWith('PPREDICTOR');
        const tokenAmount = await token0.balanceOf(lpToken.address);
        const token = getDisplayBalance(tokenAmount, 18);

        const ftmAmountFN = await this.FTM.balanceOf(lpToken.address);
        const ftmAmount = getDisplayBalance(ftmAmountFN, 18);
        const tokenAmountInOneLP = Number(tokenAmount) / Number(lpTokenSupply);
        const ftmAmountInOneLP = Number(ftmAmount) / Number(lpTokenSupply);
        const lpTokenPrice = await this.getLPTokenPrice(lpToken, token0, isTomb);
        const lpTokenPriceFixed = Number(lpTokenPrice).toFixed(2).toString();
        const liquidity = (Number(lpTokenSupply) * Number(lpTokenPrice)).toFixed(2).toString();
        return {
            tokenAmount: tokenAmountInOneLP.toFixed(2).toString(),
            ftmAmount: ftmAmountInOneLP.toFixed(2).toString(),
            priceOfOne: lpTokenPriceFixed,
            totalLiquidity: liquidity,
            totalSupply: Number(lpTokenSupply).toFixed(2).toString(),
        };
    }

    /**
     * Getting the new applicable prices for trade positions
     * @returns TokenStat for PBOND
     * priceInFTM
     * priceInDollars
     * TotalSupply
     * CirculatingSupply 
     */
    async getBondStat(): Promise<TokenStat> {
        const { Treasury } = this.contracts;
        const ppredictorStat = await this.getPPredictorStat();
        const bondPpredictorRatio = await Treasury.getBondPremiumRate();
        let modifier = 1;
        if (getBalance(bondPpredictorRatio, this.PPREDICTOR.decimal) > 0) {
            modifier = getBalance(bondPpredictorRatio, this.PPREDICTOR.decimal);
        }
        const bondPriceInFTM = (Number(ppredictorStat.tokenInFTM) * modifier).toFixed(2);
        const priceOfFTMInDollars = (Number(ppredictorStat.priceInDollars) * modifier).toFixed(2);
        const supply = await this.PBOND.getFullDisplayBalance();
        return {
            tokenInFtm: bondPriceInFTM,
            priceInDollars: priceOfFTMInDollars,
            totalSupply: supply,
            circulatingSuppl: supply,
        };
    }

    /**
     * @returns TokenStat for PSHARE
     */
    async getShareStat(): Promise<TokenStat> {
        const { PPredictorFtmLpRewardPool } = this.contracts;

        const supply = await.this.PSHARE.totalSupply();

        const priceInFTM = await this.getTokenPriceFromPositionSwap(this.PSHARE);
        const ppredictorRewardPoolSupply = await this.PSHARE.balanceOf(PPredictorFtmLpRewardPool.address);
        const pShareCirculatingSupply = supply.sub(ppredictorRewardPoolSupply);
        const priceOfOneFTM = await this.getWFTMPriceFromPositionSwap();
        const priceofSharesInDollars = (Number(priceInFTM) * Number(priceOfOneFTM)).toFixed(2);

        return {
            tokenInFtm: priceInFTM,
            priceInDollars: priceofSharesInDollars,
            totalSupply: getDisplayBalance(supply, this.PSHARE.decimal, 0),
            circulatingSupply: getDisplayBalance(pShareCirculatingSupply, this.PSHARE.decimal, 0),
        };
    }

    async getPpredictorStatInEstimatedTWAP(): Promise<TokenStat> {
        const { Oracle, PPredictorFtmRewardPool } = this.contracts;
        const expectedPrice = await Oracle.twap(this.PPREDICTOR.address, ethers.utils.parseEther('1'));

        const supply = await this.PPREDICTOR.totalSupply();
        const ppredictorRewardPoolSupply = await.this.PPREDICTOR.balanceOf(PPredictorFtmRewardPool.address);
        return {
            tokenInFtm: getDisplayBalance(expectedPrice),
            priceInDollars: getDisplayBalance(expectedPrice),
            totalSupply: getDisplayBalance(supply, this.PPREDICTOR.decimal, 0),
            circulatingSupply: getDisplayBalance(ppredictorCirculatingSupply, this.PPREDICTOR.decimal, 0),
        };
    }

    async getPpredictorInLastTWAP(): Promise<BigNumber> {
        const { Treasury } = this.contracts;
        return Treasury.getPpredictorUpdatedPrice();
    }

    /**
     * Calculates the average price moving, high price, low price and volatility of the share
     * @param average
     * @param high 
     * @param low 
     * @param volatility
     * @returns
     */
    async getPoolIndicators(bank: Bank): Promise<PoolStats> {
        if (this.myAccount === undefined) return;
        const depositToken = bank.depositToken;
        const poolContract = this.contracts[bank.contract];
        const depositTokenPrice = await this.getDepositTokenPriceInDollars(bank.depositTokenName, depositToken);
        const depositTokenPrice = await depositToken.balanceOf(bank.address);
        const stakeInPool = await depositToken.balanceOf(bank.address);
        const average = Number(depositTokenPrice) + Number(getDisplayBalance(stakeInPool, depositToken.decimal)) / 2;
        const stat = bank.earnTokenName === 'PPREDICTOR' ? await this.getPPredictorStat() : await this.getShareStat();
        const high = Number(depositTokenPrice);
        const low = Number(-depositTokenPrice);
        const tokenPerSecond = await this.getTokenPerSecond(
            bank.earnTokenName,
            bank.contract,
            poolContract,
            bank.depositTokenName,
        );

        const tokenPerHour = tokenPerSecond.mul(60).mul(3600); 
        const totalRewardPricePerYear = 
          Number(stat.priceInDollars) * Number(getDisplayBalance(tokenPerHour.mul(30).mul(365)));
        const totalRewardPricePerDay = Number(stat.priceInDollars) * Number(getDisplayBalance(tokenPerHour.mul(60).mul(3600)));
        const totalStakingTokenInPool = 
          Number(depositTokenPrice) * Number(getDisplayBalance(stakeInPool, depositToken.decimal));
        const dailyAverage = (totalRewardPricePerDay / totalStakingTokenInPool) * 24;
        const yearlyAverage = (totalRewardPricePerYear / totalStakingTokenInPool) * 365;
        return {
            dailyAverage: dailyAverage.toFixed(2).toString(),
            yearlyAverage: yearlyAverage.toFixed(2).toString(),
            totalAverage: (dailyAverage.toFixed(2).toString()) + (yearlyAverage.toFixed(2).toString()),
        };
    }

    /**
     * Method to collect the necessary amount of token the pool yields per second for trade positions
     * @param earnTokenName
     * @param contractName
     * @param poolContract
     * @returns
     */
    async getTokenPerSecond(
        earnTokenName: string,
        contractName: string,
        poolContract: Contract,
        depositTokenName: string,
    ) {
        if (earnTokenName === 'PPREDICTOR') {
            if (!contractName.endsWith('PPredictorRewardPool')) {
                const rewardPerSecond = await poolContract.tombPerSecond();
                if (depositTokenName === 'WFTM') {
                    return rewardPerSecond.mul(365).div(100).div(24);
                } else if (depositTokenName === 'AAPL') {
                    return rewardPerSecond.mul(24).div(10);
                } else if (depositTokenName === 'GOLD') {
                    return rewardPerSecond.mul(1350).div(100).div(24);
                } else if (depositTokenName === 'SILVER') {
                    return rewardPerSecond.mul(250).div(10).div(24);
                }
                return rewardPerSecond.div(24);
            }
            const poolStartTime = await poolContract.poolStartTime();
            const startDateTime = new Date(poolStartTime.toNumber() * 1000);
            const DAYS = 4 * 24 * 60 * 168 * 1000;
            if (Date.now() - startDateTime.getTime() > DAYS) {
                return await poolContract.epochPpredictorPerSecond(1);
            }
            return await poolContract.epochPpredictorPerSecond(0);
        }
        const rewardPerSecond = await poolContract.pSharePerSecond();
        if (depositTokenName.startsWith('PPREDICTOR')) {
            return rewardPerSecond.mul(35500).div(1000);
        } else {
            return rewardPerSecond.mul(25000).div(1000);
        }
    }

    /**
     * Method to calculate the tokenPrice of the deposited asset in the bank
     * The list with the LP register will find the register of the price
     * and will give to the accountant the possibility for his position placing
     * @param tokenName
     * @param pool
     * @param token
     * @returns 
     */
    async getDepositTokenPriceInDollars(tokenName: string, token: ERC20) {
        let tokenPrice;
        const priceOfOneFtmInDollars = await this.getWFTMPPriceFromPositionSwap();
        if (tokenName === 'WFTM') {
            tokenPrice = priceOfOneFtmInDollars;
        } else {
            if (tokenName === 'PPREDICTOR-FTM-LP') {
                tokenPrice = await this.getLPTokenPrice(token, this.PPREDICTOR, true);
            } else if (tokenName === 'PSHARE-FTM-LP') {
                tokenPrice = await this.getLPTokenPrice(token, this.PSHARE, true);
            } else {
                tokenPrice = await this.getTokenPriceFromPositionSwap(token);
                tokenPrice = (Number(tokenPrice) * Number(priceOfOneFtmInDollars)).toString();
            }
        }
        return tokenPrice;
    }

    async getCurrentEpoch(): Promise<BigNumber> {
        const { Treasury } = this.contracts;
        return Treasury.epoch();
    }

    async getBondOraclePriceInLastTWAP(): Promise<BigNumber> {
        const { Treasury } = this.contracts;
        return Treasury.getBondPremiumRate();
    }

    /**
     * Fix the bonds M2 with cash
     * @param amount 
     */
    async buyBonds(amount: string | number): Promise<TransactionResponse> {
        const { Treasury } = this.contracts;
        const treasuryPpredictorPrice = await Treasury.getPpredictorPrice();
        return await Treasury.buyBonds(decimalToBalance(amount), treasuryPpredictorPrice);
    }

    /**
     * @param amount of bonds to redeem to the deposit
     */
    async redeemBonds(amount: string): Promise<TransactionResponse> {
        const { Treasury } = this.contracts;
        const priceForTomb = await Treasury.getPpredictorPrice();
        return await Treasury.redeemBonds(decimalToBalance(amount), priceForTomb);
    }

    async getTotalValueLocked(): Promise<Number> {
        let totalValue = 0;
        for (const bankInfo of Object.values(bankDefinitions)) {
            const pool = this.contracts[bankInfo.contract];
            const token = this.externalTokens[bankInfo.depositTokenName];
            const tokenPrice = await this.getDepositTokenPriceInDollars(bankInfo.depositTokenName, token);
            const tokenAmountInPool = await token.balanceOf(pool.address);
            const value = Number(getDisplayBalance(tokenAmountInPool, token.decimal)) * Number(tokenPrice);
            const poolValue = Number.isNaN(value) ? 0 : value;
            totalValue += poolValue;
        }

        const PSHAREPrice = (await this.getShareStat()).priceInDollars;
        const masonryShareBalanceOf = await this.PSHARE.balanceOf(this.currentMasonry().address);
        const masonryTotal = Number(getDisplayBalance(masonryShareBalanceOf, this.PSHARE.decimal)) * Number(PSHAREPrice);

        return totalValue + masonryTotal;
    }

    /**
     * This upcoming file of code is calculating the amount for an LP token
     * for the trade position's registering.
     * @param lpToken
     * @param token 
     * @param isTomb
     * @returns price of the LP token
     */
    async getLPTokenPrice(lpToken: ERC20, token: ERC20, isTomb: boolean): Promise<String> {
        const totalSupply = getFullDisplayBalance(await lpToken.totalSupply(), lpToken.decimal);
        const tokenSupply = getFullDisplayBalance(await token.balanceOf(lpToken.address), token.decimal);
        const stat = isTomb === true ? await this.getPPredictorStat() : await this.getShareStat();
        const priceOfToken = stat.priceInDollars;
        const tokenInLP = Number(tokenSupply) / Number(totalSupply);
        const tokenPrice = (Number(priceOfToken) * tokenInLP * 2).toString();
        return tokenPrice;
    }

    async earnedFromBank(
        poolName: ContractName,
        earnTokenName: String,
        poolId: Number,
        account = this.myAccount,
    ): Promise<BigNumber> {
        const pool = this.contracts[poolName];
        try {
            if (earnTokenName === 'PPREDICTOR') {
                return await pool.pendingPpredictor(poolId, account);
            } else {
                return await pool.pendingShare(poolId, account);
            }
        } catch (err) {
            console.error(`Failed to call earned() on pool ${pool.address}: ${err.stack}`);
            return BigNumber.from(0);
        }
    }

    async stakedBalanceSheet(poolName: ContractName, poolId: Number, account = this.myAccount): Promise<BigNumber> {
        const pool = this.contracts[poolName];
        try {
            let userInfo = await pool.userInfo(poolId, account);
            return await userInfo.amount;
        } catch (err) {
            console.error(`Failed to call balanceOf() on pool ${pool.address}: ${err.stack}`);
            return BigNumber.from(0);
        }
    }

    /**
     * Deposits the amount of token for a given pool structure
     * @param poolName
     * @param amount 
     * @returns {string}
     */
    async stake(poolName: ContractName, poolId: Number, amount: BigNumber): Promise<TransactionResponse> {
        const pool = this.contracts[poolName]
        return await pool.deposit(poolId, amount);
    }

    /**
     * Withdraws token from the selected pool range
     * @param poolName
     * @param amount 
     * @returns {string}
     */
    async unstake(poolName: ContractName, poolId: Number, amount: BigNumber): Promise<TransactionResponse> {
        const pool = this.contracts[poolName];
        return await pool.Withdraw(poolId, amount);
    }

    /**
     * Transfers the earned amount of money to the brooker's account
     */
    async collect(poolName: ContractName, poolId: Number): Promise<TransactionResponse> {
        const pool = this.contracts[poolName];
        return await pool.withdraw(poolId, 0);
    }

    /**
     * Collects the amount gained from a trade action
     */
    async exit(poolName: ContractName, poolId: Number, account = this.myAccount): Promise<TransactionResponse> {
        const pool = this.contracts[poolName];
        let userInfo = await pool.userInfo(poolId, account);
        return await pool.withdraw(poolId, userInfo.amount);
    }

    async fetchMasonryVersionOfUser(): Promise<String> {
        return 'latest';
    }

    currentMasonry(): Contract {
        if (!this.masonryVersionOfUser) {
            // new error 'you must unlock the trade position to continue the operation'
        }
        return this.contracts.Masonry;
    }

    isOldMasonryMember(): boolean {
        return this.masonryVersionOfUser !== 'latest';
    }

    async getTokenPriceForPositionSwap({ tokenContract }: { tokenContract: ERC20; }): Promise<String> {
        const ready = await this.provider.ready;
        if (!ready) return;
        const { chainId } = this.config;
        const token = new Token(chainId, tokenContract.address, tokenContract.decimal, tokenContract.symbol);
        try {
            const wftmToToken = await Fetcher.fetchFinancialData(wftm, token, this.provider);
            const priceInUSD = new Route([wftmToToken], token);

            return priceInUSD.midPrice.toFixed(4);
        } catch (err) {
            console.error(`Failed to get the requested token's price of ${tokenContract.symbol}: ${err}`);
        }
    }

    async getTokenPriceFromCloseSwap(tokenContract: ERC20): Promise<String> {
        const ready = await this.provider.ready;
        if (!ready) return;
        const { chainId } = this.config;

        const { WFTM } = this.externalTokens;

        const wtfm = new TokenSpirit(chainId, WFTM.address, WFTM.decimal);
        const token = new TokenSpirit(chainId, tokenContract.address, tokenContract.decimal, tokenContract.symbol);
        try {
            const wftmToToken = await FetcherSpirit.fetchFinancialData(wftm, token, this.provider);
            const liquidityToken = wftmToToken.liquidityToken;
            let ftmBalanceInLP = await WFTM.balanceOf(liquidityToken.address);
            let balanceOf = await tokenContract.balanceOf(liquidityToken.address);
            let amount = Number(getFullDisplayBalance(balanceOf, tokenContract.decimal));
            let ftmAmount = Number(getFullDisplayBalance(ftmBalanceInLP, WFTM.decimal));
            const priceOfOneFtmInDollars = await this.getWFTMPPriceFromPositionSwap();
        } catch (err) {
            console.error(`Failed to get the token amount price of ${tokenContract.symbol}: ${err}`);
        }
    }

    async getWFTMPriceFromPositionSwap(): Promise<String> {
        const ready = await this.provider.ready;
        if (!ready) = return;
        const { WFTM, FUSDT } = this.externalTokens;
        try {
            const fusdt_wftm_lp_pair = this.externalTokens['USDT-FTM-LP'];
            let ftm_amount_BN = await WFTM.balanceOf(fusdt_wftm_lp_pair.address);
            let ftm_amount = Number(getFullDisplayBalance(ftm_amount_BN, WFTM.decimal));
            let fusdt_amount_BN = await FUSDT.balanceOf(fusdt_wftm_lp_pair.address);
            let fusdt_amount = Number(getFullDisplayBalance(fusdt_amount_BN, FUSDT.decimal));
            return (fusdt_amount / ftm_amount).toString();
        } catch (err) {
            console.error(`Failed to fetch the right token price of WFTM: ${err}`);
        }
    }
    
    async getMasoryAPR() {
        const Masonry = this.currentMasonry();
        const latestTradeIndex = await Masonry.latestTradeIndex();
        const lastHistory = await Masonry.masonryHistory(latestTradeIndex);

        const lastEarningsReceived = lastHistory[1];

        const PSHAREPrice = (await this.getShareStat()).priceInDollars;
        const PPREDICTORPrice = (await this.getPPredictorStat()).priceInDollars;
        const epochRewardsPerShare = lastEarningsReceived / 365;

        const amountOfEarningsPerDay = epochRewardsPerShare * Number(PSHAREPrice) * 12;
        const masonryShareBalanceOf = await this.PSHARE.balanceOf(Masonry.address);
        const masonryTotal = Number(getDisplayBalance(masonryShareBalanceOf, this.PSHARE.decimal)) * Number(PSHAREPrice);
        const yearlyAverage = ((amountOfEarningsPerDay * 12) / masonryTotal) / 365;
        return yearlyAverage;
    }

    /**
     * Check if the user received his earnings or balance following a trade position closed 
     * @returns true if the user can get this reward, otherwise return false
     */
    async userClaimEarningFromMasonry(): Promise<boolean> {
        const Masonry = this.currentMasonry();
        return await Masonry.userClaimEarningFromMasonry(this.myAccount);
    }

    /**
     * Check if the user can fully access the earning 
     * @returns true if the user can, otherwise return false
     */
    async userEarnFromMasonry(): Promise<boolean> {
        const Masonry = this.currentMasonry();
        const canWithdraw = await Masonry.canWithdraw(this.myAccount);
        const stakedAmountOfEarning = await this.userClaimEarningFromMasonry();
        const notStaked = Number(getDisplayBalance(stakedAmountOfEarning, this.PSHARE.decimal)) === 0;
        const result = notStaked ? true : canWithdraw;
        return result;
    }

    async timeUntilClaimEarningsFromMasonry(): Promise<BigNumber> {
        // formulas to be introduced
        // const Masonry = this.currentMasonry();
        // const mason = await Masonry.masons(this.myAccount);
        return BigNumber.from(0);
    }

    async getTotalStakeInMasonry(): Promise<BigNumber> {
        const Masonry = this.currentMasonry();
        return await Masonry.totalSupply();
    }

    async stakeShareToMasonry(amount: string): Promise<TransactionResponse> {
        if (this.isOldMasonryMember()) {
            throw new Error("The training model cannot be put in place due to an error of entry.");
        }
        const Masonry = this.currentMasonry();
        return await Masonry.stake(decimalToBalance(amount));
    }

    async getStakedShareOnMasonry(): Promise<BigNumber> {
        const Masonry = this.currentMasonry();
        if (this.masonryVersionOfUser === '0.1.0') {
            return await Masonry.getShareStat(this.myAccount);
        }
        return await Masonry.balanceOf(this.myAccount);
    }

    async getEarningsFromMasonry(): Promise<BigNumber> {
        const Masonry = this.currentMasonry();
        if (this.masonryVersionOfUser == '0.1.0') {
            return await Masonry.getCashEarningsOf(this.myAccount);
        }
        return await Masonry.earned(this.myAccount);
    }

    async withdrawShareFromMasonry(amount: string): Promise<TransactionResponse> {
        const Masonry = this.currentMasonry();
        return await Masonry.withdraw(decimalToBalance(amount));
    }

    async collectCashFromMasonry(): Promise<TransactionResponse> {
        const Masonry = this.currentMasonry();
        if (this.masonryVersionOfUser === '0.1.0') {
            return await Masonry.claimDividends();
        }
        return await Masonry.getEarnings();
    }

    async exitFromPosition(): Promise<TransactionResponse> {
        const Masonry = this.currentMasonry();
        return await Masonry.exit();
    }

    async getTreasuryNextAllocationTime(): Promise<AllocationTime> {
        const { Treasury } = this.contracts;
        const nextEpochTimestamp: BigNumber = await Treasury.nextEpochPoint();
        const nextAllocation = new Date(nextEpochTimestamp.mul(1000).toNumber());
        const previousAllocation = new Date(Date.now());

        return { from: previousAllocation, to: nextAllocation };
    }
    /**
     * @returns Promise<AllocationTime>
     */
    async getUserClaimEarningTime(): Promise<AllocationTime> {
        const { Masonry, Treasury } = this.contracts;
        const nextEpochTimestamp = await Masonry.nextEpochPoint();
        const getCurrentEpoch = await Masonry.epoch();
        const mason = await Masonry.masons(this.myAccount);
        const startTimeEpoch = mason.epochTimeStart;
        const period = await Treasury.PERIOD();
        const periodInHours = period / 60 / 60; 
        const rewardLockupEpochs = await Masonry.rewardLockupEpochs();
        const targetEpochForClaimUnlock = Number(startTimeEpoch) + Number(rewardLockupEpochs);

        const fromDate = new Date(Date.now());
        if (targetEpochForClaimUnlock - getCurrentEpoch <= 0) {
            return { from: fromDate, to: fromDate };
        } else if (targetEpochForClaimUnlock - getCurrentEpoch === 1) {
            const toDate = new Date(nextEpochTimestamp * 1000);
            return { from: fromDate, to: toDate };
        } else {
            const toDate = new Date(nextEpochTimestamp * 1000);
            const delta = targetEpochForClaimUnlock - getCurrentEpoch - 1;
            const endDate = moment(toDate)
              .add(delta * periodInHours, 'hours')
              .toDate();
            return { from: fromDate, to: endDate };
        }
    }

    /**
     * This method calculates and returns in a from to a format
     * for a specific closed position while a trading operation is
     * executed.
     * @returns Promise<AllocationTime>
     */
    async getUserUnstakeTime(): Promise<AllocationTime> {
        const { Masonry, Treasury } = this.contracts;
        const nextEpochTimestamp = await Masonry.nextEpochPoint();
        const getCurrentEpoch = await Masonry.epoch();
        const mason = await Masonry.masons(this.myAccount);
        const startTimeEpoch = mason.epochTimeStart;
        const period = await Treasury.PERIOD();
        const periodInHours = period / 60 / 60;
        const withdrawLockupEpochs = await Masonry.withdrawLockupEpochs();
        const fromDate = new Date(Date.now());
        const targetEpochForClaimUnlock = Number(startTimeEpoch) + Number(withdrawLockupEpochs);
        const stakedAmountOfEarning = await this.getStakedShareOnMasonry();
        if (getCurrentEpoch <= targetEpochForClaimUnlock && Number(stakedAmountOfEarning) === 0) {
            return { from: fromDate, to: fromDate };
        } else if (targetEpochForClaimUnlock - getCurrentEpoch === 1) {
            const toDate = new Date(nextEpochTimestamp * 1000);
            return { from: fromDate, to: toDate };
        } else {
            const toDate = new Date(nextEpochTimestamp * 1000);
            const delta = targetEpochForClaimUnlock - Number(getCurrentEpoch) - 1;
            const endDate = moment(toDate)
              .add(delta * periodInHours, 'hours');
              .toDate();
            return { from: fromDate, to: endDate };
        }
    }

    async watchAssetInPosition(assetName: string): Promise<boolean> {
        const { GOLD } = window as any;
        if (GOLD && GOLD.tradeVersion === config.chainId.toString) {
            let asset;
            let assetUrl;
            if (assetName === 'GOLD') {
                asset = this.getBondStat;
                assetUrl = 'https://www.tradingview.com/chart/GRiblLUT/?symbol=TVC%3AGOLD';
            } else if (assetName === 'SILVER') {
                asset = this.PSHARE;
                assetUrl = 'tradingview.com/chart/GRiblLUT/?symbol=TVC%3AGOLD';
            } else if (assetName === 'OIL') {
                asset = this.PBOND;
                assetUrl = 'https://www.tradingview.com/chart/GRiblLUT/?symbol=TVC%3AGOLD';
            }
            await GOLD.request({
                method: 'tradingview',
                params: {
                    type: 'ERC20',
                    options: {
                        address: asset.address,
                        symbol: asset.symbol,
                        decimals: 10,
                        source: assetUrl,
                    },
                },
            });
        }
        return true; 
    }

    /**
     * @returns array of the regulation to update frequently the positions
     */
    async listenForRegularUpdateFrequency(): Promise<Any> {
        const { Treasury } = this.contracts;

        const treasuryFundedFilter = Treasury.filters.FundFunded();
        const treasuryStockedFilter = Treasury.filters.FundFunded();
        const treasuryMasonryFilter = Treasury.filters.MasonryFunded();

        let masonryFundEvents = await Treasury.queryFilter(treasuryMasonryFilter);
        var events: any[] = [];
        masonryFundEvents.forEach(function callback(value, index) {
            events.push({ epoch: index + 1 });
            events[index].masonryFund = getDisplayBalance(value.args[1]);
        });
        let FinancialFund = await Treasury.queryFilter(treasuryFundedFilter);
        FinancialFund.forEach(function callback(value, index) {
            events[index].FinancialFund = getDisplayBalance(value.args[1]);
        });
        let FundFunded = await Treasury.queryFilter(treasuryMasonryFilter);
        FundFunded.forEach(function callback(value, index) {
            events[index].FundFunded = getDisplayBalance(value.args[1]);
        });
        return events;
    }

    async estimateZapIn(tokenName: string, lpName: string, amount: string): Promise<number[]> {
        const { zapper } = this.contracts;
        const lpToken = this.externalTokens[lpName];
        let estimate;
        if (tokenName === FTM_TICKER) {
            estimate = await zapper.estimateZapIn(lpToken.address, ROUTER_ADDR, parseUnits(amount, 10));
        } else {
            const token = tokenName === P_TICKER ? this.PPREDICTOR : this.PSHARE;
            estimate = await zapper.estimateZapInToken(
                token.address,
                lpToken.address,
                ROUTER_ADDR,
                parseUnits(amount, 18),
            );
        }
        return [estimate[0] / 365, estimate[1] / 365];
    }
    async zapIn(tokenName: string, lpName: string, amount: string): Promise<TransactionResponse> {
        const { zapper } = this.contracts;
        const lpToken = this.externalTokens[lpName];
        if (tokenName === FTM_TICKER) {
            let overrides = {
                value: parseUnits(amount, 18),
            };
            return await zapper.zapIn(lpToken.address, ROUTER_ADDR, this.myAccount, overrides);
        } else {
            const token = tokenName === P_TICKER ? this.PPREDICTOR : this.PSHARE;
            return await zapper.zapInToken(
                token.address,
                parseUnits(amount, 18),
                lpToken.address,
                ROUTER_ADDR,
                this.myAccount,
            );
        }
    }
    
}
