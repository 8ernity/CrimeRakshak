package com.example.crimerakshak

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import com.example.crimerakshak.viewmodel.OverviewViewModel

val PrimaryGreen = Color(0xFFa3d73c)
val BackgroundDark = Color(0xFF11150b)
val SurfaceDark = Color(0xFF1a1d14)
val TextLight = Color(0xFFe1e4d3)
val TextMuted = Color(0xFF8c9383)

@Composable
fun OverviewScreen(
    modifier: Modifier = Modifier,
    viewModel: OverviewViewModel = viewModel()
) {
    val state by viewModel.uiState.collectAsState()
    
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(BackgroundDark)
            .verticalScroll(rememberScrollState())
            .padding(16.dp)
    ) {
        // Top Bar (Profile + Name)
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.fillMaxWidth().padding(bottom = 24.dp)
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(CircleShape)
                    .background(Color.DarkGray),
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Filled.Person, contentDescription = "Profile", tint = Color.LightGray)
            }
            Spacer(modifier = Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text("TACTICAL COMMAND", color = TextMuted, fontSize = 10.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                Text("Welcome, Officer Miller", color = TextLight, fontSize = 18.sp, fontWeight = FontWeight.Bold)
            }
            Icon(Icons.Filled.Star, contentDescription = null, tint = PrimaryGreen, modifier = Modifier.size(24.dp))
        }

        // Header
        Text("Executive Snapshot", color = TextLight, fontSize = 22.sp, fontWeight = FontWeight.Bold)
        Text("Real-time jurisdictional overview", color = TextMuted, fontSize = 14.sp, modifier = Modifier.padding(bottom = 16.dp))

        // Chips Row
        if (state.isLoading) {
            CircularProgressIndicator(color = PrimaryGreen, modifier = Modifier.padding(bottom = 16.dp))
        } else {
            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.padding(bottom = 16.dp)
            ) {
                val chips = state.districts.take(4).mapIndexed { index, district -> 
                    district.name to (index == 0) 
                }
                items(chips) { (text, isSelected) ->
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(16.dp))
                            .background(if (isSelected) PrimaryGreen else SurfaceDark)
                            .padding(horizontal = 16.dp, vertical = 8.dp)
                    ) {
                        Text(text.uppercase(), color = if (isSelected) BackgroundDark else TextMuted, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }

        // Predictive Alert Card
        Card(
            colors = CardDefaults.cardColors(containerColor = SurfaceDark),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(bottom = 8.dp)) {
                    Icon(Icons.Filled.Warning, contentDescription = null, tint = PrimaryGreen, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("PREDICTIVE ALERT", color = PrimaryGreen, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
                Text("High Risk of Property Crime in Sector 7", color = TextLight, fontSize = 18.sp, fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(bottom = 16.dp))
                
                Button(
                    onClick = { },
                    colors = ButtonDefaults.buttonColors(containerColor = PrimaryGreen, contentColor = BackgroundDark),
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Icon(Icons.Filled.Security, contentDescription = null, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("DEPLOY PATROL 42B", fontWeight = FontWeight.Bold, fontSize = 12.sp)
                }
            }
        }

        // Governance SLA Card
        Card(
            colors = CardDefaults.cardColors(containerColor = SurfaceDark),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(bottom = 16.dp)) {
                    Icon(Icons.Filled.AdminPanelSettings, contentDescription = null, tint = TextMuted, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("GOVERNANCE SLA", color = TextMuted, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
                Row(horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp)) {
                    Text("FIR Compliance", color = TextLight, fontSize = 16.sp)
                    Text("98%", color = PrimaryGreen, fontSize = 36.sp, fontWeight = FontWeight.Bold)
                }
                Row(horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
                    Text("Audit Log", color = TextMuted, fontSize = 14.sp)
                    Box(modifier = Modifier.border(1.dp, PrimaryGreen.copy(alpha = 0.5f), RoundedCornerShape(4.dp)).padding(horizontal = 8.dp, vertical = 4.dp)) {
                        Text("VERIFIED", color = PrimaryGreen, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }

        // 2x2 Grid Stats
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp)) {
            // Total Crimes
            Card(
                colors = CardDefaults.cardColors(containerColor = SurfaceDark),
                modifier = Modifier.weight(1f).aspectRatio(1f)
            ) {
                Column(modifier = Modifier.padding(16.dp).fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
                    Text("TOTAL CRIMES", color = TextMuted, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                    Text(String.format("%,d", state.totalCrimes), color = TextLight, fontSize = 32.sp, fontWeight = FontWeight.Bold)
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Filled.ArrowDownward, contentDescription = null, tint = PrimaryGreen, modifier = Modifier.size(12.dp))
                        Text("-5% YOY", color = PrimaryGreen, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
            // IPC Cases
            Card(
                colors = CardDefaults.cardColors(containerColor = SurfaceDark),
                modifier = Modifier.weight(1f).aspectRatio(1f)
            ) {
                Column(modifier = Modifier.padding(16.dp).fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
                    Text("IPC CASES", color = TextMuted, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                    val totalIpc = state.districts.sumOf { it.ipc }
                    Text(String.format("%,d", totalIpc), color = TextLight, fontSize = 32.sp, fontWeight = FontWeight.Bold)
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Filled.PieChart, contentDescription = null, tint = TextMuted, modifier = Modifier.size(12.dp))
                        Spacer(modifier = Modifier.width(4.dp))
                        val share = if (state.totalCrimes > 0) (totalIpc * 100 / state.totalCrimes) else 0
                        Text("$share% SHARE", color = TextMuted, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }

        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp)) {
            // Resolution Rate
            Card(
                colors = CardDefaults.cardColors(containerColor = SurfaceDark),
                modifier = Modifier.weight(1f).aspectRatio(1f)
            ) {
                Column(modifier = Modifier.padding(16.dp).fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
                    Text("RESOLUTION RATE", color = TextMuted, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                    Text("84%", color = PrimaryGreen, fontSize = 32.sp, fontWeight = FontWeight.Bold)
                    // Progress bar
                    Box(modifier = Modifier.fillMaxWidth().height(4.dp).background(Color.DarkGray)) {
                        Box(modifier = Modifier.fillMaxWidth(0.84f).fillMaxHeight().background(PrimaryGreen))
                    }
                }
            }
            // Jurisdictions
            Card(
                colors = CardDefaults.cardColors(containerColor = SurfaceDark),
                modifier = Modifier.weight(1f).aspectRatio(1f)
            ) {
                Column(modifier = Modifier.padding(16.dp).fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
                    Text("JURISDICTIONS", color = TextMuted, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                    Text("12", color = TextLight, fontSize = 32.sp, fontWeight = FontWeight.Bold)
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Filled.Map, contentDescription = null, tint = TextMuted, modifier = Modifier.size(12.dp))
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("ACTIVE\nMONITORED", color = TextMuted, fontSize = 10.sp, fontWeight = FontWeight.Bold, lineHeight = 12.sp)
                    }
                }
            }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Dynamic SQL-powered Charts
        DashboardCharts(state)
        
        Spacer(modifier = Modifier.height(32.dp))
    }
}
