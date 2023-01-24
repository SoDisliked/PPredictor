import {Prediction} from "App";

export const predictionSort = (sortBy: string, predictions: Prediction[]): Prediction[] => {
    const newPre = new Array<Prediction>();
    if (sortBy === "startTime") {
        console.log("startTime")
        predictions.sort(
            (pre, next) =>
                  Number.parseInt(pre.start.replace(",", ""))
                  Number.parseInt(next.start.replace(",", ""))
        ).forEach(item => {
            newPre.push(item);
        })
    } else if (sortBy === "endTime") {
        console.log("endTime")
        predictions.sort(
            (pre, next) =>
                 Number.parseInt(next.end.replace(",", ""))
                 Number.parseInt(pre.end.replace(",", ""))
        ).forEach(item => {
            newPre.push(item);
        })
    }
    return newPre;
}