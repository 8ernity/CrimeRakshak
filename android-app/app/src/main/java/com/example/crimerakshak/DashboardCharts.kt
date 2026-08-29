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
                    text = "CRIME CATEGORY BREAKDOWN", 
                    color = TextMuted, 
                    fontSize = 12.sp, 
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp,
                    modifier = Modifier.padding(bottom = 16.dp)
                )
                
                if (state.pieChartData.isNotEmpty()) {
                    val row = state.pieChartData.first()
                    
                    val categories = listOf(
                        "Murder" to ((row["murder"] as? Number)?.toFloat() ?: 0f),
                        "Attempt to Murder" to ((row["attempt_to_murder"] as? Number)?.toFloat() ?: 0f),
                        "Rape" to ((row["rape"] as? Number)?.toFloat() ?: 0f),
                        "Dacoity" to ((row["dacoity"] as? Number)?.toFloat() ?: 0f),
                        "Robbery" to ((row["robbery"] as? Number)?.toFloat() ?: 0f),
                        "Burglary" to ((row["burglary"] as? Number)?.toFloat() ?: 0f),
                        "Theft" to ((row["theft"] as? Number)?.toFloat() ?: 0f),
                        "Riots" to ((row["riots"] as? Number)?.toFloat() ?: 0f),
                        "Cases of Hurt" to ((row["cases_of_hurt"] as? Number)?.toFloat() ?: 0f),
                        "Cruelty by Husband" to ((row["cruelty_by_husband"] as? Number)?.toFloat() ?: 0f),
                        "Dowry Deaths" to ((row["dowry_deaths"] as? Number)?.toFloat() ?: 0f),
                        "Fatal Motor Accidents" to ((row["fatal_motor_accidents"] as? Number)?.toFloat() ?: 0f),
                        "Non-Fatal Motor Accidents" to ((row["non_fatal_motor_accidents"] as? Number)?.toFloat() ?: 0f),
                        "Molestation" to ((row["molestation"] as? Number)?.toFloat() ?: 0f),
                        "SC/ST Act" to ((row["sc_st"] as? Number)?.toFloat() ?: 0f),
                        "Gambling" to ((row["gambling"] as? Number)?.toFloat() ?: 0f),
                        "DP Act" to ((row["dp_act"] as? Number)?.toFloat() ?: 0f),
                        "Cyber Crime" to ((row["cyber_crime"] as? Number)?.toFloat() ?: 0f),
                        "POCSO" to ((row["pocso"] as? Number)?.toFloat() ?: 0f),
                        "POCSO Rape" to ((row["pocso_rape"] as? Number)?.toFloat() ?: 0f)
                    ).filter { it.second > 0f }.sortedByDescending { it.second }

                    val top8 = categories.take(8)
                    val otherTotal = categories.drop(8).sumOf { it.second.toDouble() }.toFloat()
                    
                    val finalCategories = top8.toMutableList()
                    if (otherTotal > 0f) {
                        finalCategories.add("Other Categories" to otherTotal)
                    }

                    val total = categories.sumOf { it.second.toDouble() }.toFloat()
                    
                    val chartPalette = listOf(
                        Color(0xFF6366f1), Color(0xFFa855f7), Color(0xFFec4899), Color(0xFFf43f5e), 
                        Color(0xFFf97316), Color(0xFFeab308), Color(0xFF84cc16), Color(0xFF22c55e), 
                        Color(0xFF06b6d4), Color(0xFF3b82f6)
                    )
                    
                    val pieChartData = PieChartData(
                        slices = finalCategories.mapIndexed { index, pair ->
                            PieChartData.Slice(pair.first, pair.second, chartPalette[index % chartPalette.size])
                        },
                        plotType = co.yml.charts.common.model.PlotType.Donut
                    )
                    val pieChartConfig = PieChartConfig(
                        isAnimationEnable = true,
                        showSliceLabels = false,
                        animationDuration = 1500,
                        activeSliceAlpha = .9f,
                        isEllipsizeEnabled = true,
                        backgroundColor = SurfaceDark,
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
                    Column(
                        modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        finalCategories.chunked(3).forEach { rowItems ->
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceEvenly
                            ) {
                                rowItems.forEachIndexed { index, item ->
                                    val globalIndex = finalCategories.indexOf(item)
                                    LegendItem(item.first, chartPalette[globalIndex % chartPalette.size])
                                }
                            }
                        }
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
                    text = "MONTHLY CRIME VOLUME", 
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
                        .bottomPadding(20.dp)
                        .startDrawPadding(20.dp)
                        .axisLabelColor(TextMuted)
                        .axisLineColor(Color.Transparent)
                        .axisLabelFontSize(10.sp)
                        .backgroundColor(Color.Transparent)
                        .labelData { index -> barList.getOrNull(index)?.label?.take(3) ?: "" }
                        .build()
                        
                    val yAxisData = AxisData.Builder()
                        .steps(5)
                        .axisLabelColor(TextMuted)
                        .axisLineColor(Color.Transparent)
                        .labelAndAxisLinePadding(10.dp)
                        .axisLabelFontSize(10.sp)
                        .backgroundColor(Color.Transparent)
                        .labelData { i ->
                            val max = barList.maxOfOrNull { it.point.y } ?: 0f
                            val stepValue = if (max == 0f) 1f else max / 5
                            (i * stepValue).toInt().toString()
                        }.build()
                        
                    val barChartData = BarChartData(
                        chartData = barList,
                        xAxisData = xAxisData,
                        yAxisData = yAxisData,
                        backgroundColor = Color.Transparent,
                        barStyle = BarStyle(paddingBetweenBars = 15.dp, barWidth = 16.dp, cornerRadius = 4.dp),
                        horizontalExtraSpace = 10.dp
                    )
                    Box(modifier = Modifier.height(200.dp).fillMaxWidth().padding(horizontal = 4.dp)) {
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
                    text = "TOP 10 DISTRICTS - CRIME VOLUME", 
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
                        .bottomPadding(20.dp)
                        .startDrawPadding(20.dp)
                        .labelData { i -> topDistricts.getOrNull(i)?.name?.take(3)?.uppercase() ?: "" }
                        .labelAndAxisLinePadding(10.dp)
                        .axisLabelColor(TextMuted)
                        .axisLineColor(Color.Transparent)
                        .axisLabelFontSize(10.sp)
                        .backgroundColor(Color.Transparent)
                        .build()
                        
                    val yAxisData = AxisData.Builder()
                        .steps(5)
                        .labelAndAxisLinePadding(10.dp)
                        .axisLabelColor(TextMuted)
                        .axisLineColor(Color.Transparent)
                        .axisLabelFontSize(10.sp)
                        .backgroundColor(Color.Transparent)
                        .labelData { i ->
                            val max = points.maxOfOrNull { it.y } ?: 0f
                            val stepValue = if (max == 0f) 1f else max / 5
                            (i * stepValue).toInt().toString()
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
                    Box(modifier = Modifier.height(200.dp).fillMaxWidth().padding(horizontal = 4.dp)) {
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
