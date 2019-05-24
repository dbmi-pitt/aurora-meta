!function(){
	var nvdiscreteBarChart={}, nvPieChart={}, nvmultiBarHorizontal={};

	nvdiscreteBarChart.draw=function(data) {
		 nv.addGraph(function() {
    			var chart = nv.models.discreteBarChart()
    				.x(function(d) { return d.label })
    				.y(function(d) { return d.value })
    				.showValues(true)
                    .valueFormat(d3.format(',d'));

			    chart.tooltip.enabled();

                 chart.yAxis
                    .tickFormat(d3.format(',d'));

                //chart.height(300);
    			//d3.select('#chart svg')
                d3.select('#age-chart')
        			.datum(data)
        			.call(chart);

    			nv.utils.windowResize(chart.update);
	    return chart;
  		});
	}

    nvPieChart.draw = function(data, id) {
        nv.addGraph(function() {
            var height = 500;
            var width = 500;
            var chart = nv.models.pieChart()
                .x(function(d) { return d.label })
                .y(function(d) { return d.value })
                .margin({top: 5, right: 5, bottom: 5, left: 150})  //.margin({top: 15, right: 5, bottom: 15, left: 50})
                .width(width)
                .height(height)
                .labelType("percent");
//                .showTooltipPercent(true);

            //d3.select("#piechart svg")
            d3.select(id)
                .datum(data)
                .transition().duration(1200)
                .attr('width', width)
                .attr('height', height)
                .call(chart);
        return chart;
    });

    }

    nvmultiBarHorizontal.draw = function(data, id, ileft) {
        nv.addGraph(function() {
            var left = ileft
            var height = 400;
//            var width = 500;
            var chart = nv.models.multiBarHorizontalChart()
                .x(function(d) { return d.label })
                .y(function(d) { return d.value })
                .margin({top: 0, right: 5, bottom: 50, left: 300})   //.margin({top: 15, right: 5, bottom: 20, left: 50})
                .showValues(true)           //Show bar value next to each bar.
                .showControls(false)        //Allow user to switch between "Grouped" and "Stacked" mode.
                .valueFormat(d3.format(',d'));

            chart.barColor(['#6666FF', '#FFB399', '#FF33FF', '#FFFF99', '#00B3E6', 
                            '#E6B333', '#3366E6', '#999966', '#99FF99', '#B34D4D',
                            '#80B300', '#809900', '#E6B3B3', '#6680B3', '#66991A', 
                            '#FF99E6', '#CCFF1A', '#FF1A66', '#E6331A', '#33FFCC',
                            '#66994D', '#B366CC', '#4D8000', '#B33300', '#CC80CC', 
                            '#66664D', '#991AFF', '#E666FF', '#4DB3FF', '#1AB399',
                            '#E666B3', '#33991A', '#CC9999', '#B3B31A', '#00E680', 
                            '#4D8066', '#809980', '#E6FF80', '#1AFF33', '#999933',
                            '#FF3380', '#CCCC00', '#66E64D', '#4D80CC', '#9900B3', 
                            '#E64D66', '#4DB380', '#FF4D4D', '#99E6E6', '#6666FF']);
            chart.yAxis
                .tickFormat(d3.format(',d'));

            chart.tooltip.enabled();                

            d3.select(id)
                .datum(data)
//                .attr('width', width)
                .attr('height', height)                
                .call(chart);

            nv.utils.windowResize(chart.update);

        return chart;
        });
    }

	this.nvdiscreteBarChart = nvdiscreteBarChart;
    this.nvPieChart = nvPieChart;
    this.nvmultiBarHorizontal = nvmultiBarHorizontal;
}();