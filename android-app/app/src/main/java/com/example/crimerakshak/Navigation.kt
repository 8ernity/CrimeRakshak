package com.example.crimerakshak

import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.Box
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Dashboard
import androidx.compose.material.icons.filled.SmartToy
import androidx.compose.material.icons.filled.Map

@Composable
fun MainNavigation() {
    var selectedTab by remember { mutableStateOf(0) }

    Scaffold(
        bottomBar = {
            NavigationBar(
                containerColor = Color(0xFF191d13),
                contentColor = Color(0xFFe1e4d3)
            ) {
                NavigationBarItem(
                    icon = { Icon(Icons.Filled.Dashboard, contentDescription = "Overview") },
                    label = { Text("Overview") },
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = Color(0xFF9acd32),
                        selectedTextColor = Color(0xFF9acd32),
                        indicatorColor = Color(0xFF33362b),
                        unselectedIconColor = Color(0xFFc3c9b1),
                        unselectedTextColor = Color(0xFFc3c9b1)
                    )
                )
                NavigationBarItem(
                    icon = { Icon(Icons.Filled.Map, contentDescription = "Map") },
                    label = { Text("Map") },
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = Color(0xFF9acd32),
                        selectedTextColor = Color(0xFF9acd32),
                        indicatorColor = Color(0xFF33362b),
                        unselectedIconColor = Color(0xFFc3c9b1),
                        unselectedTextColor = Color(0xFFc3c9b1)
                    )
                )
                NavigationBarItem(
                    icon = { Icon(Icons.Filled.SmartToy, contentDescription = "Copilot") },
                    label = { Text("Copilot") },
                    selected = selectedTab == 2,
                    onClick = { selectedTab = 2 },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = Color(0xFF9acd32),
                        selectedTextColor = Color(0xFF9acd32),
                        indicatorColor = Color(0xFF33362b),
                        unselectedIconColor = Color(0xFFc3c9b1),
                        unselectedTextColor = Color(0xFFc3c9b1)
                    )
                )
            }
        }
    ) { innerPadding ->
        Box(modifier = Modifier.padding(innerPadding)) {
            when (selectedTab) {
                0 -> OverviewScreen()
                1 -> MapScreen()
                2 -> CopilotScreen()
            }
        }
    }
}
