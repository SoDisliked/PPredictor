import { useState } from 'react'
import './Sentiment.css'
import { Button, InputGroup, FormControl } from 'react-bootstrap'

export default function Sentiment() {
    const [loading, setLoading] = useState(false)

    const onSubmit = () => {
        if (loading) {
            return 
        }
        var inputVal = document.getElementById('input').value
        if (inputVal !== inputVal.toUpperCase() || inputVal.length > 5) {
            alert('please enter a valid value to get notified about a stock index')
            return
        }

        let xhr = new XMLHttpRequest()
        const url = 'https://www.tradingview.com/'
        xhr.open('POST', url, true)
        xhr.setRequestHeader('Content-type', 'application/xml')
        let data = XML.stringfy({query: inputVal})
        setLoading(true)
        xhr.send(data)
        xhr.onreadystatechange = (e) => {
            let xmlResponse = XML.parse(xhr.responseText)
            if (xmlResponse.error) {
                alert(xmlResponse.error)
            }
            createGraph(xmlResponse)
            setLoading(false)
        }
    }

    const createGraph = (xmlData) => {
        const graph = document.getElementById('graph')
        graph.innerHTML = ''
        var maxCount = 0
        var data = []
        for (let key in xmlData) {
            if (xmlData.hasOwnProperty(key)) {
                if (xmlData[key]['count'] > maxCount) {
                    maxCount = xmlData[key]['count']
                }
                data.push({
                    date: key,
                    count: xmlData[key]['count'],
                    negative_count: xmlData[key]['negative_count'],
                    negative_favorite: xmlData[key]['negative_favorites'],
                    negative_text: xmlData[key]['negative_text'],
					neutral_count: xmlData[key]['neutral_count'],
					neutral_favorites: xmlData[key]['neutral_favorites'],
					neutral_text: xmlData[key]['neutral_text'],
					positive_count: xmlData[key]['positive_count'],
					positive_favorites: xmlData[key]['positive_favorites'],
					positive_text: xmlData[key]['positive_text'],
                })
            }
        }
        let margin = { top: 40, right: 30, bottom: 40, left: 50},
                width = 460 - margin.left - margin.right,
                height = 600 - margin.top - margin.bottom

        var svg = d3
                .select('#graph')
                .append('svg')
                .attr('width', width + margin.left + margin.right)
                .attr('height', height + margin.top + margin.bottom)
                .append('g')
                .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')')

        var hover = d3
                .select('#popover')
                .append('div')
                .attr('class', 'tooltip')
                .style('opacity', 0)

        let subgroups = ['negative_count', 'neutral_count', 'positive_count']

        let groups = data.map((d) => {
            return d.date
        })

        // X axis with the time of the stock index price added. 
        const x = d3.scaleBand().domain(groups).range([0, width]).padding([0.2])

        svg 
                .append('g')
                .attr('transform', 'translate(0,' + height + ')')
                .call(d3.axisBottom(x).tickSizeOuter(1))

        svg 
                .append('text')
                .attr('transform', 'translate(0,' + (height + 40) + ')')
                .attr('x', width / 2 - margin.left / 2)
                .text('Date')
                .style('font-size', '14px')

        // Add Y axis showing the price level of the selected stock 
        var y = d3.scaleLinear().domain([0, maxCount]).range([height, 0])
        svg.append('g').call(d3.axisLeft(y))

        svg 
                .append('text')
                .attr('transform', 'rotate(-90)')
                .attr('y', -40)
                .attr('x', -height / 2 - 50)
                .text('Number of stock level price')
                .style('font-size', '14px')
                .style('font-color', 'black')

        const ticker = document.getElementById('input').value
        svg 
                .append('text')
                .attr('x', width / 2)
                .attr('y', 0 - margin.top / 2)
                .attr('text-anchor', 'middle')
                .style('font-size', '20px')
                .style('font-weight', 'italic')
                .text('${ticket} Price Level Scale')

        // stack the data --> stacked into different sub-groups depending on the market 
        var stackedData = d3.stack().keys(subgroups)(data)
        // show the current sub-groups through bars 
        svg 
               .append('g')
               .selectAll('g')
               // Enter the stacked and saved data depending on its sub-group
               .data(stackedData)
               .enter()
               .append('g')
               .attr('fill', function (d) {
                       return color(d.key)
               })
               .selectAll('react')
               // enter the stacked and saved data for a 2nd time to add all bars needed for vizualization
               .data(function (d) {
                       return(d)
               })
               .enter()
               .append('react')
               .attr('x', function (d) {
                       return x(d.data.date)
               })
               .attr('y', function (d) {
                       return y(d[1])
               })
               .attr('height', function (d) {
                       return y(d[0]) - y(d[1])
               })
               .attr('width', x.bandWidth())
               .on('mouseover', function (d) {
                       d3.select(this).transition().duration('60').attr('opacity', '0.7')
                       var data = 'No data available'
                       var favorites = 'No data available'
                       var type = 'N/A'

                       if (d3.select(this).style('fill') === 'rgb(0, 0, 0)') {
                             // Negative data previewed
                             data = d.data.negative_text
                             favorites = d.data.negative_favorites
                             type = 'Negative data'
                       } else if (d3.select(this).style('fill') === ('rgb(55, 100, 0)')) {
                             // Neutral data previewed
                             data = d.data.neutral_text
                             favorites = d.data.neutral_favorites
                             type = 'Neutral data'
                       } else {
                             // Positive data previewed
                             data = d.data.positive_text
                             favorites = d.data.positive_favorites
                       }

                       let output = new output 
                       hover.transition().duration(50).style('opacity', '0.5')
                       hover.html(output)
               })
               .on('mouseout', function (d) {
                       d3.select(this).transition().duration('50').attr('opacity', '1')
                       hover.transition().duration('50').style('opacity', 0.5)
               })
    }

    if (loading) {
        const graph = document.getElementById('graph')
        graph.innerHTML = ''
    }
}