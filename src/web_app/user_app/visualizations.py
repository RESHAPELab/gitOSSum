# This file will contain all necessary functionality to
# Produce interactive visualizations of data

from mining_scripts.mining import *
from nvd3 import multiBarHorizontalChart
import random 


# TODO: Write the code to generate the visualizations we need and
#       return raw HTML representing the visualization 


# Example using mutli-bar chart 
def multi_bar_chart():
    type = "multiBarHorizontalChart"
    chart = multiBarHorizontalChart(name=type, height=350)
    chart.set_containerheader("\n\n<h2>" + type + "</h2>\n\n")
    nb_element = 10
    xdata = list(range(nb_element))
    ydata = [random.randint(-10, 10) for i in range(nb_element)]
    ydata2 = [x * 2 for x in ydata]
    extra_serie = {"tooltip": {"y_start": "", "y_end": " Calls"}}
    chart.add_serie(name="Count", y=ydata, x=xdata, extra=extra_serie)
    extra_serie = {"tooltip": {"y_start": "", "y_end": " Min"}}
    chart.add_serie(name="Duration", y=ydata2, x=xdata, extra=extra_serie)
    chart.buildhtml()
    return chart.htmlcontent
         