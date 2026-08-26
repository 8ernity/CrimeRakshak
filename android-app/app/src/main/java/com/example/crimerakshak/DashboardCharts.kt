package com.example.crimerakshak

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
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
import co.yml.charts.ui.linechart.model.LineType
import co.yml.charts.ui.linechart.model.SelectionHighlightPoint
import co.yml.charts.ui.linechart.model.ShadowUnderLine
import com.example.crimerakshak.viewmodel.OverviewState
import co.yml.charts.common.model.Point as YChartPoint
import co.yml.charts.axis.AxisData
import co.yml.charts.ui.linechart.model.IntersectionPoint
import co.yml.charts.ui.linechart.model.LinePlotData
import co.yml.charts.ui.linechart.model.LineStyle

@Composable
fun DashboardCharts(state: OverviewState) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        // Crime Category Breakdown Donut Chart
        Card(
            colors = CardDefaults.cardColors(containerColor = SurfaceDark),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = "CRIME CATEGORY BREAKDOWN (2025)", 
                    color = TextMuted, 
                    fontSize = 12.sp, 
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp,
                    modifier = Modifier.padding(bottom = 16.dp)
                )
                
                if (state.pieChartData.isNotEmpty()) {
                    val row = state.pieChartData.first()
                    val theft = (row["theft"] as? Number)?.toFloat() ?: 0f
                    val robbery = (row["robbery"] as? Number)?.toFloat() ?: 0f
                    val burglary = (row["burglary"] as? Number)?.toFloat() ?: 0f
                    val cyberCrime = (row["cyber_crime"] as? Number)?.toFloat() ?: 0f
                    val murder = (row["murder"] as? Number)?.toFloat() ?: 0f
                    val total = theft + robbery + burglary + cyberCrime + murder
                    
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
                        strokeWidth = 35f
                    )
                    Box(modifier = Modifier.height(200.dp).fillMaxWidth(), contentAlignment = Alignment.Center) {
                        Box(modifier = Modifier.size(200.dp)) {
                            DonutPieChart(
                                modifier = Modifier.fillMaxSize(),
                                pieChartData = pieChartData,
                                pieChartConfig = pieChartConfig
                            )
                        }
                        // Center text
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            val formattedTotal = if (total > 1000) String.format("%.1fk", total / 1000f) else total.toInt().toString()
                            Text(text = formattedTotal, color = TextLight, fontSize = 24.sp, fontWeight = FontWeight.Bold)
                            Text(text = "TOTAL", color = TextMuted, fontSize = 10.sp, letterSpacing = 1.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                    
                    // Legend
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
                        horizontalArrangement = Arrangement.SpaceEvenly,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        LegendItem("Theft", Color(0xFFa3d73c))
                        LegendItem("Robbery", Color(0xFFe1e4d3))
                        LegendItem("Burglary", Color(0xFF8c9383))
                        LegendItem("Cyber Crime", Color(0xFF4caf50))
                        LegendItem("Murder", Color(0xFFf44336))
                    }
                }
            }
        }
        
        // Monthly Crime Volume Bar Chart
        Card(
            colors = CardDefaults.cardColors(containerColor = SurfaceDark),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = "MONTHLY CRIME VOLUME (2025)", 
                    color = TextMuted, 
                    fontSize = 12.sp, 
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp,
                    modifier = Modifier.padding(bottom = 16.dp)
                )
                
                if (state.barChartData.isNotEmpty()) {
                    val barList = state.barChartData.mapIndexed { index, map ->
                        val count = (map["current_month"] as? Number)?.toFloat() ?: 0f
                        BarData(point = YChartPoint(index.toFloat(), count), label = map["crime_head"]?.toString() ?: "", color = Color(0xFFa3d73c))
                    }
                    
                    val xAxisData = AxisData.Builder()
                        .axisStepSize(40.dp)
                        .steps(barList.size - 1)
                        .bottomPadding(130.dp)
                        .startDrawPadding(20.dp)
                        .axisLabelColor(TextMuted)
                        .axisLineColor(Color.Transparent)
                        .axisLabelFontSize(10.sp)
                        .axisLabelAngle(270f)
                        .backgroundColor(Color.Transparent)
                        .labelData { index -> barList.getOrNull(index)?.label ?: "" }
                        .build()
                        
                    val yAxisData = AxisData.Builder()
                        .steps(5)
                        .axisLabelColor(TextMuted)
                        .axisLineColor(Color.Transparent)
                        .labelAndAxisLinePadding(25.dp)
                        .axisLabelFontSize(10.sp)
                        .backgroundColor(Color.Transparent)
                        .labelData { i ->
                            val max = barList.maxOfOrNull { it.point.y } ?: 0f
                            val stepValue = if (max == 0f) 1f else max / 5
                            (i * stepValue).toInt().toString() + "  "
                        }.build()
                        
                    val barChartData = BarChartData(
                        chartData = barList,
                        xAxisData = xAxisData,
                        yAxisData = yAxisData,
                        backgroundColor = Color.Transparent,
                        barStyle = BarStyle(paddingBetweenBars = 15.dp, barWidth = 16.dp, cornerRadius = 4.dp),
                        horizontalExtraSpace = 10.dp
                    )
                    Box(modifier = Modifier.height(260.dp).fillMaxWidth().padding(horizontal = 4.dp)) {
                        BarChart(modifier = Modifier.fillMaxSize(), barChartData = barChartData)
                    }
                }
            }
        }
        
        // Top 10 Districts Line/Area Chart
        Card(
            colors = CardDefaults.cardColors(containerColor = SurfaceDark),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = "TOP 10 DISTRICTS - CRIME VOLUME (2025)", 
                    color = TextMuted, 
                    fontSize = 12.sp, 
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp,
                    modifier = Modifier.padding(bottom = 16.dp)
                )
                
                if (state.districts.isNotEmpty()) {
                    val topDistricts = state.districts.sortedByDescending { it.total }.take(10)
                    
                    val points = topDistricts.mapIndexed { index, d ->
                        YChartPoint(index.toFloat(), d.total.toFloat())
                    }
                    
                    val xAxisData = AxisData.Builder()
                        .axisStepSize(40.dp)
                        .steps(points.size - 1)
                        .bottomPadding(130.dp)
                        .startDrawPadding(20.dp)
                        .labelData { i -> topDistricts.getOrNull(i)?.name?.uppercase() ?: "" }
                        .labelAndAxisLinePadding(10.dp)
                        .axisLabelColor(TextMuted)
                        .axisLineColor(Color.Transparent)
                        .axisLabelFontSize(10.sp)
                        .axisLabelAngle(270f)
                        .backgroundColor(Color.Transparent)
                        .build()
                        
                    val yAxisData = AxisData.Builder()
                        .steps(5)
                        .labelAndAxisLinePadding(25.dp)
                        .axisLabelColor(TextMuted)
                        .axisLineColor(Color.Transparent)
                        .axisLabelFontSize(10.sp)
                        .backgroundColor(Color.Transparent)
                        .labelData { i ->
                            val max = points.maxOfOrNull { it.y } ?: 0f
                            val stepValue = if (max == 0f) 1f else max / 5
                            (i * stepValue).toInt().toString() + "  "
                        }.build()
                        
                    val lineChartData = LineChartData(
                        linePlotData = LinePlotData(
                            lines = listOf(
                                Line(
                                    dataPoints = points,
                                    lineStyle = LineStyle(
                                        color = Color(0xFFa3d73c),
                                        lineType = LineType.SmoothCurve()
                                    ),
                                    intersectionPoint = IntersectionPoint(
                                        color = BackgroundDark, 
                                        radius = 3.dp,
                                    ),
                                    SelectionHighlightPoint(color = Color(0xFFa3d73c)),
                                    ShadowUnderLine(
                                        alpha = 0.3f,
                                        brush = androidx.compose.ui.graphics.Brush.verticalGradient(
                                            colors = listOf(Color(0xFFa3d73c), Color.Transparent)
                                        )
                                    )
                                )
                            )
                        ),
                        xAxisData = xAxisData,
                        yAxisData = yAxisData,
                        backgroundColor = Color.Transparent
                    )
                    Box(modifier = Modifier.height(260.dp).fillMaxWidth().padding(horizontal = 4.dp)) {
                        LineChart(modifier = Modifier.fillMaxSize(), lineChartData = lineChartData)
                    }
                }
            }
        }
    }
}

@Composable
fun LegendItem(label: String, color: Color) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(modifier = Modifier.size(8.dp).clip(CircleShape).background(color))
        Spacer(modifier = Modifier.width(6.dp))
        Text(text = label, color = TextLight, fontSize = 12.sp)
    }
}
