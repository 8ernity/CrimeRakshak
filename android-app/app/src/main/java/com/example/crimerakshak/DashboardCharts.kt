package com.example.crimerakshak

import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import co.yml.charts.ui.barchart.BarChart
import co.yml.charts.ui.barchart.models.BarChartData
import co.yml.charts.ui.barchart.models.BarData
import co.yml.charts.ui.barchart.models.BarStyle
import co.yml.charts.ui.piechart.charts.DonutPieChart
import co.yml.charts.ui.piechart.models.PieChartConfig
import co.yml.charts.ui.piechart.models.PieChartData
import co.yml.charts.ui.linechart.LineChart
import co.yml.charts.ui.linechart.model.Line
import co.yml.charts.ui.linechart.model.LineChartData

import com.example.crimerakshak.viewmodel.OverviewState
import co.yml.charts.common.model.Point as YChartPoint
import co.yml.charts.axis.AxisData
import co.yml.charts.ui.linechart.model.IntersectionPoint
import co.yml.charts.ui.linechart.model.LinePlotData
import co.yml.charts.ui.linechart.model.LineStyle

@Composable
fun DashboardCharts(state: OverviewState) {
    Column(modifier = Modifier.fillMaxWidth()) {
        Text("CRIME CATEGORY BREAKDOWN", color = TextMuted, fontSize = 12.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(bottom = 16.dp))
        
        if (state.pieChartData.isNotEmpty()) {
            val row = state.pieChartData.first()
            val theft = (row["theft"] as? Number)?.toFloat() ?: 0f
            val robbery = (row["robbery"] as? Number)?.toFloat() ?: 0f
            val burglary = (row["burglary"] as? Number)?.toFloat() ?: 0f
            val cyberCrime = (row["cyber_crime"] as? Number)?.toFloat() ?: 0f
            val murder = (row["murder"] as? Number)?.toFloat() ?: 0f
            
            val pieChartData = PieChartData(
                slices = listOf(
                    PieChartData.Slice("Theft", theft, Color(0xFFa3d73c)),
                    PieChartData.Slice("Robbery", robbery, Color(0xFFe1e4d3)),
                    PieChartData.Slice("Burglary", burglary, Color(0xFF8c9383)),
                    PieChartData.Slice("Cyber Crime", cyberCrime, Color(0xFF4caf50)),
                    PieChartData.Slice("Murder", murder, Color(0xFFf44336))
                ),
                plotType = co.yml.charts.common.model.PlotType.Donut
            )
            val pieChartConfig = PieChartConfig(
                isAnimationEnable = true,
                showSliceLabels = false,
                animationDuration = 1500,
                activeSliceAlpha = .9f,
                isEllipsizeEnabled = true,
                backgroundColor = Color.Transparent,
                strokeWidth = 60f
            )
            Box(modifier = Modifier.height(240.dp).fillMaxWidth().padding(horizontal = 32.dp, vertical = 16.dp)) {
                DonutPieChart(
                    modifier = Modifier.fillMaxSize(),
                    pieChartData = pieChartData,
                    pieChartConfig = pieChartConfig
                )
            }
        }
        
        Spacer(modifier = Modifier.height(32.dp))
        Text("MONTHLY CRIME VOLUME", color = TextMuted, fontSize = 12.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(bottom = 16.dp))
        
        if (state.barChartData.isNotEmpty()) {
            val barList = state.barChartData.mapIndexed { index, map ->
                val count = (map["current_month"] as? Number)?.toFloat() ?: 0f
                BarData(point = YChartPoint(index.toFloat(), count), label = map["crime_head"]?.toString() ?: "", color = Color(0xFFa3d73c))
            }
            
            val xAxisData = AxisData.Builder()
                .axisStepSize(40.dp)
                .steps(barList.size - 1)
                .bottomPadding(40.dp)
                .axisLabelColor(TextMuted)
                .axisLineColor(TextMuted)
                .axisLabelFontSize(10.sp)
                .backgroundColor(Color.Transparent)
                .labelData { index -> barList.getOrNull(index)?.label?.take(4) ?: "" }
                .build()
                
            val yAxisData = AxisData.Builder()
                .steps(5)
                .axisLabelColor(TextMuted)
                .axisLineColor(TextMuted)
                .labelAndAxisLinePadding(10.dp)
                .axisLabelFontSize(10.sp)
                .backgroundColor(Color.Transparent)
                .labelData { i ->
                    val max = barList.maxOfOrNull { it.point.y } ?: 0f
                    val stepValue = max / 5
                    (i * stepValue).toInt().toString()
                }.build()
                
            val barChartData = BarChartData(
                chartData = barList,
                xAxisData = xAxisData,
                yAxisData = yAxisData,
                backgroundColor = Color.Transparent,
                barStyle = BarStyle(paddingBetweenBars = 15.dp)
            )
            Box(modifier = Modifier.height(260.dp).fillMaxWidth()) {
                BarChart(modifier = Modifier.fillMaxSize(), barChartData = barChartData)
            }
        }
        
        Spacer(modifier = Modifier.height(32.dp))
        Text("TOP 10 DISTRICTS - CRIME VOLUME", color = TextMuted, fontSize = 12.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(bottom = 16.dp))
        
        if (state.districts.isNotEmpty()) {
            val topDistricts = state.districts.sortedByDescending { it.total }.take(10)
            
            val points = topDistricts.mapIndexed { index, d ->
                YChartPoint(index.toFloat(), d.total.toFloat())
            }
            
            val xAxisData = AxisData.Builder()
                .axisStepSize(40.dp)
                .steps(points.size - 1)
                .labelData { i -> topDistricts.getOrNull(i)?.name?.take(3) ?: "" }
                .labelAndAxisLinePadding(10.dp)
                .axisLabelColor(TextMuted)
                .axisLineColor(TextMuted)
                .axisLabelFontSize(10.sp)
                .backgroundColor(Color.Transparent)
                .build()
                
            val yAxisData = AxisData.Builder()
                .steps(5)
                .labelAndAxisLinePadding(10.dp)
                .axisLabelColor(TextMuted)
                .axisLineColor(TextMuted)
                .axisLabelFontSize(10.sp)
                .backgroundColor(Color.Transparent)
                .labelData { i ->
                    val max = points.maxOfOrNull { it.y } ?: 0f
                    val stepValue = max / 5
                    (i * stepValue).toInt().toString()
                }.build()
                
            val lineChartData = LineChartData(
                linePlotData = LinePlotData(
                    lines = listOf(
                        Line(
                            dataPoints = points,
                            lineStyle = LineStyle(color = Color(0xFFa3d73c)),
                            intersectionPoint = IntersectionPoint(color = Color(0xFFa3d73c), radius = 2.dp)
                        )
                    )
                ),
                xAxisData = xAxisData,
                yAxisData = yAxisData,
                backgroundColor = Color.Transparent
            )
            Box(modifier = Modifier.height(260.dp).fillMaxWidth()) {
                LineChart(modifier = Modifier.fillMaxSize(), lineChartData = lineChartData)
            }
        }
    }
}
