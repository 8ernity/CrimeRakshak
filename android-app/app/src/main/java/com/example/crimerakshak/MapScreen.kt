package com.example.crimerakshak

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.zIndex
import androidx.compose.ui.viewinterop.AndroidView
import android.location.Geocoder
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextAlign
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.osmdroid.config.Configuration
import org.osmdroid.tileprovider.tilesource.OnlineTileSourceBase
import org.osmdroid.tileprovider.tilesource.TileSourceFactory
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.MapView
import org.osmdroid.views.CustomZoomButtonsController
import org.osmdroid.views.overlay.Polygon
import android.graphics.DashPathEffect

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MapScreen(modifier: Modifier = Modifier) {
    val Primary = Color(0xFF9ACD32)
    val GlassBg = Color(0xD91E1E1E) // 85% opacity #1E1E1E
    val GlassBorder = Color(0x0DFFFFFF) // 5% opacity white
    
    var showMapTypeSheet by remember { mutableStateOf(false) }
    var currentMapType by remember { mutableStateOf("Default") }
    var crimeFilter by remember { mutableStateOf("ALL") } // ALL, VIOLENT, CYBER, NARCOTICS
    var shiftFilter by remember { mutableStateOf("DAY") } // DAY, NIGHT
    var overlayMode by remember { mutableStateOf("FILL") } // FILL, BORDERS
    val context = LocalContext.current
    
    Box(
        modifier = modifier
            .fillMaxSize()
            .background(Color(0xFF11150b))
    ) {
        var mapView by remember { mutableStateOf<MapView?>(null) }
        val coroutineScope = rememberCoroutineScope()
        
        // Background Map
        AndroidView(
            factory = { ctx ->
                Configuration.getInstance().load(ctx, ctx.getSharedPreferences("osmdroid", android.content.Context.MODE_PRIVATE))
                Configuration.getInstance().userAgentValue = context.packageName
                
                MapView(ctx).apply {
                    mapView = this
                    setMultiTouchControls(true)
                    zoomController.setVisibility(CustomZoomButtonsController.Visibility.NEVER)
                    
                    // Center over Karnataka
                    controller.setZoom(7.5)
                    controller.setCenter(GeoPoint(15.3173, 75.7139))
                    this.maxZoomLevel = 18.0
                    this.minZoomLevel = 5.0
                    
                    loadGeoJsonOverlay(ctx, this)
                }
            },
            update = { view ->
                when (currentMapType) {
                    "Default" -> {
                        val voyagerTileSource = object : OnlineTileSourceBase(
                            "Voyager", 1, 19, 256, ".png",
                            arrayOf("https://a.basemaps.cartocdn.com/rastertiles/voyager/")
                        ) {
                            override fun getTileURLString(pMapTileIndex: Long): String {
                                return "$baseUrl${org.osmdroid.util.MapTileIndex.getZoom(pMapTileIndex)}/${org.osmdroid.util.MapTileIndex.getX(pMapTileIndex)}/${org.osmdroid.util.MapTileIndex.getY(pMapTileIndex)}$mImageFilenameEnding"
                            }
                        }
                        view.setTileSource(voyagerTileSource)
                    }
                    "Satellite" -> {
                        val esriTileSource = object : OnlineTileSourceBase(
                            "ESRI", 1, 18, 256, "",
                            arrayOf("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/")
                        ) {
                            override fun getTileURLString(pMapTileIndex: Long): String {
                                return "$baseUrl${org.osmdroid.util.MapTileIndex.getZoom(pMapTileIndex)}/${org.osmdroid.util.MapTileIndex.getY(pMapTileIndex)}/${org.osmdroid.util.MapTileIndex.getX(pMapTileIndex)}"
                            }
                        }
                        view.setTileSource(esriTileSource)
                    }
                    "Dark GIS" -> {
                        val darkGisTileSource = object : OnlineTileSourceBase(
                            "DarkGIS", 1, 19, 256, ".png",
                            arrayOf("https://a.basemaps.cartocdn.com/dark_all/")
                        ) {
                            override fun getTileURLString(pMapTileIndex: Long): String {
                                return "$baseUrl${org.osmdroid.util.MapTileIndex.getZoom(pMapTileIndex)}/${org.osmdroid.util.MapTileIndex.getX(pMapTileIndex)}/${org.osmdroid.util.MapTileIndex.getY(pMapTileIndex)}$mImageFilenameEnding"
                            }
                        }
                        view.setTileSource(darkGisTileSource)
                    }
                }
                
                // Update Heatmap Polygons
                view.overlays.filterIsInstance<Polygon>().forEach { polygon ->
                    val districtName = polygon.title ?: ""
                    val riskTier = getAdjustedRiskTier(districtName, crimeFilter, shiftFilter)
                    
                    // Exact colors from design-tokens.ts with 8% opacity (20 alpha) for fill
                    val (fillColor, outlineColor) = when (riskTier) {
                        "Critical" -> Pair(android.graphics.Color.argb(20, 244, 63, 94), android.graphics.Color.parseColor("#f43f5e")) // Red
                        "High" -> Pair(android.graphics.Color.argb(20, 251, 146, 60), android.graphics.Color.parseColor("#fb923c")) // Orange
                        "Moderate" -> Pair(android.graphics.Color.argb(20, 245, 158, 11), android.graphics.Color.parseColor("#f59e0b")) // Amber
                        else -> Pair(android.graphics.Color.argb(20, 16, 185, 129), android.graphics.Color.parseColor("#10b981")) // Green
                    }
                    
                    polygon.fillPaint.color = if (overlayMode == "BORDERS") android.graphics.Color.TRANSPARENT else fillColor
                    polygon.outlinePaint.color = outlineColor
                    polygon.outlinePaint.strokeWidth = if (overlayMode == "BORDERS") 3f else 2f
                    polygon.outlinePaint.pathEffect = DashPathEffect(floatArrayOf(15f, 20f), 0f)
                }
                view.invalidate()
            },
            modifier = Modifier.fillMaxSize()
        )

        // Top UI Overlay
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 32.dp) // Shifted slightly upwards
                .zIndex(10f)
        ) {
            // Search Bar
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp) // Slimmer width
                    .height(56.dp), // Standard Material Search Bar Height
                shape = CircleShape,
                color = Color(0xFF303134), // Solid dark gray matching Google Maps dark mode
                shadowElevation = 8.dp
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        Icons.Outlined.Search, 
                        contentDescription = "Search",
                        tint = Color(0xFFA1A1AA),
                        modifier = Modifier.padding(start = 4.dp).size(24.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    
                    var searchText by remember { mutableStateOf("") }
                    
                    fun performSearch() {
                        if (searchText.isBlank()) return
                        coroutineScope.launch(Dispatchers.IO) {
                            try {
                                val geocoder = Geocoder(context, java.util.Locale.getDefault())
                                @Suppress("DEPRECATION")
                                val results = geocoder.getFromLocationName("$searchText, Karnataka", 1)
                                if (!results.isNullOrEmpty()) {
                                    val location = results[0]
                                    withContext(Dispatchers.Main) {
                                        mapView?.controller?.animateTo(GeoPoint(location.latitude, location.longitude), 12.0, 1000)
                                    }
                                }
                            } catch (e: Exception) { e.printStackTrace() }
                        }
                    }

                    TextField(
                        value = searchText,
                        onValueChange = { searchText = it },
                        placeholder = { Text("Search here", color = Color(0xFFA1A1AA), fontSize = 16.sp) },
                        colors = TextFieldDefaults.colors(
                            focusedContainerColor = Color.Transparent,
                            unfocusedContainerColor = Color.Transparent,
                            focusedIndicatorColor = Color.Transparent,
                            unfocusedIndicatorColor = Color.Transparent,
                            cursorColor = Primary,
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White
                        ),
                        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
                        keyboardActions = KeyboardActions(onSearch = { performSearch() }),
                        modifier = Modifier.weight(1f).fillMaxHeight(),
                        singleLine = true
                    )
                    
                    IconButton(onClick = { performSearch() }) {
                        Icon(Icons.Outlined.Mic, contentDescription = "Voice", tint = Color(0xFFA1A1AA), modifier = Modifier.size(24.dp))
                    }
                    
                    Image(
                        painter = painterResource(id = R.drawable.officer_profile),
                        contentDescription = "Profile",
                        contentScale = ContentScale.Crop,
                        modifier = Modifier
                            .size(32.dp)
                            .clip(CircleShape)
                    )
                }
            }
            
            // Action Chips
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .horizontalScroll(rememberScrollState())
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Overlay Mode Toggle
                Surface(
                    color = Color(0xFF1E2128),
                    shape = CircleShape,
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF334155))
                ) {
                    Row(modifier = Modifier.padding(2.dp)) {
                        Surface(
                            onClick = { overlayMode = "FILL" },
                            color = if (overlayMode == "FILL") Color(0xFF8B5CF6) else Color.Transparent,
                            shape = CircleShape
                        ) {
                            Text("🎨 Color Fill", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Medium, modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp))
                        }
                        Surface(
                            onClick = { overlayMode = "BORDERS" },
                            color = if (overlayMode == "BORDERS") Color(0xFF8B5CF6) else Color.Transparent,
                            shape = CircleShape
                        ) {
                            Text("🔲 Borders Only (Clear View)", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Medium, modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp))
                        }
                    }
                }
                
                // Crime filters moved to floating controls
                
                // Shift Filter Custom Toggle
                Row(verticalAlignment = Alignment.CenterVertically) {
                    val isDay = shiftFilter == "DAY"
                    val thumbOffset by androidx.compose.animation.core.animateDpAsState(if (isDay) 4.dp else 36.dp)
                    val trackColor by androidx.compose.animation.animateColorAsState(if (isDay) Color(0xFF87CEEB) else Color(0xFF1E293B))
                    val thumbColor by androidx.compose.animation.animateColorAsState(if (isDay) Color(0xFFFFD27D) else Color(0xFF94A3B8))
                    
                    Text(
                        "Day", 
                        color = if (isDay) Color(0xFF87CEEB) else Color.Gray, 
                        fontSize = 12.sp, 
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    
                    Box(
                        modifier = Modifier
                            .width(64.dp)
                            .height(32.dp)
                            .clip(CircleShape)
                            .background(trackColor)
                            .clickable { shiftFilter = if (isDay) "NIGHT" else "DAY" }
                    ) {
                        // Thumb
                        Box(
                            modifier = Modifier
                                .offset(x = thumbOffset, y = 4.dp)
                                .size(24.dp)
                                .clip(CircleShape)
                                .background(thumbColor)
                        )
                        // Cloud streaks for Day
                        if (isDay) {
                            Box(modifier = Modifier.offset(x = 34.dp, y = 10.dp).size(width = 12.dp, height = 2.dp).clip(CircleShape).background(Color.White))
                            Box(modifier = Modifier.offset(x = 30.dp, y = 15.dp).size(width = 16.dp, height = 2.dp).clip(CircleShape).background(Color.White))
                            Box(modifier = Modifier.offset(x = 38.dp, y = 20.dp).size(width = 10.dp, height = 2.dp).clip(CircleShape).background(Color.White))
                        }
                    }
                    
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        "Night", 
                        color = if (!isDay) Color.White else Color.Gray, 
                        fontSize = 12.sp, 
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
        
        // Floating Controls Right
        Column(
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(end = 16.dp, top = 164.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Map Type Layer Button
            Surface(
                onClick = { showMapTypeSheet = true },
                modifier = Modifier.size(48.dp),
                shape = CircleShape,
                color = Color(0xFF303134),
                shadowElevation = 6.dp
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(Icons.Outlined.Layers, contentDescription = "Layers", tint = Color.White, modifier = Modifier.size(24.dp))
                }
            }
            
            // Crime Filter Dropdown
            var showCrimeDropdown by remember { mutableStateOf(false) }
            val filters = listOf("ALL" to "All Crimes", "VIOLENT" to "Violent / Dacoity", "CYBER" to "Cyber & Fraud", "NARCOTICS" to "NDPS Narcotics")
            val currentFilterLabel = filters.find { it.first == crimeFilter }?.second ?: "All Crimes"
            
            Box {
                Surface(
                    onClick = { showCrimeDropdown = true },
                    modifier = Modifier.size(48.dp),
                    shape = CircleShape,
                    color = Color(0xFF303134),
                    shadowElevation = 6.dp
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(Icons.Outlined.FilterAlt, contentDescription = "Crime Filters", tint = Color.White, modifier = Modifier.size(24.dp))
                    }
                }
                
                androidx.compose.material3.DropdownMenu(
                    expanded = showCrimeDropdown,
                    onDismissRequest = { showCrimeDropdown = false },
                    modifier = Modifier.background(Color(0xFF1E2128))
                ) {
                    filters.forEach { (id, label) ->
                        androidx.compose.material3.DropdownMenuItem(
                            text = { 
                                Text(
                                    text = label, 
                                    color = if (crimeFilter == id) Primary else Color.White,
                                    fontWeight = if (crimeFilter == id) FontWeight.Bold else FontWeight.Normal
                                ) 
                            },
                            onClick = {
                                crimeFilter = id
                                showCrimeDropdown = false
                            }
                        )
                    }
                }
            }
        }
    }
    
    // Bottom Sheet for Map Type
    if (showMapTypeSheet) {
        ModalBottomSheet(
            onDismissRequest = { showMapTypeSheet = false },
            containerColor = Color(0xFF1E2128),
            scrimColor = Color.Black.copy(alpha = 0.5f)
        ) {
            Column(modifier = Modifier.fillMaxWidth().padding(16.dp)) {
                Text("Map type", color = Color.White, fontSize = 18.sp, fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(bottom = 24.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    // Default
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Surface(
                            onClick = { currentMapType = "Default"; showMapTypeSheet = false },
                            shape = RoundedCornerShape(12.dp),
                            color = Color.Transparent,
                            border = if (currentMapType == "Default") androidx.compose.foundation.BorderStroke(2.dp, Primary) else null
                        ) {
                            Image(painter = painterResource(id = R.drawable.map_default), contentDescription = "Default", modifier = Modifier.size(72.dp).clip(RoundedCornerShape(12.dp)))
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Text("Default", color = if (currentMapType == "Default") Primary else Color.White, fontSize = 14.sp)
                    }
                    
                    // Satellite
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Surface(
                            onClick = { currentMapType = "Satellite"; showMapTypeSheet = false },
                            shape = RoundedCornerShape(12.dp),
                            color = Color.Transparent,
                            border = if (currentMapType == "Satellite") androidx.compose.foundation.BorderStroke(2.dp, Primary) else null
                        ) {
                            Image(painter = painterResource(id = R.drawable.map_satellite), contentDescription = "Satellite", modifier = Modifier.size(72.dp).clip(RoundedCornerShape(12.dp)))
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Text("Satellite", color = if (currentMapType == "Satellite") Primary else Color.White, fontSize = 14.sp)
                    }
                    
                    // Dark GIS
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Surface(
                            onClick = { currentMapType = "Dark GIS"; showMapTypeSheet = false },
                            shape = RoundedCornerShape(12.dp),
                            color = Color.Transparent,
                            border = if (currentMapType == "Dark GIS") androidx.compose.foundation.BorderStroke(2.dp, Primary) else null
                        ) {
                            Image(painter = painterResource(id = R.drawable.map_dark_gis), contentDescription = "Dark GIS", modifier = Modifier.size(72.dp).clip(RoundedCornerShape(12.dp)))
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Text("Dark GIS", color = if (currentMapType == "Dark GIS") Primary else Color.White, fontSize = 14.sp)
                    }
                }
                Spacer(modifier = Modifier.height(32.dp))
            }
        }
    }
}

private fun loadGeoJsonOverlay(context: android.content.Context, mapView: MapView) {
    try {
        val inputStream = context.resources.openRawResource(R.raw.karnataka_districts)
        val jsonString = inputStream.bufferedReader().use { it.readText() }
        val featureCollection = org.json.JSONObject(jsonString)
        val features = featureCollection.getJSONArray("features")
        
        val colors = listOf(
            android.graphics.Color.argb(76, 255, 69, 58),   // Red
            android.graphics.Color.argb(76, 255, 159, 10),  // Orange
            android.graphics.Color.argb(76, 48, 209, 88),   // Green
            android.graphics.Color.argb(76, 10, 132, 255)   // Blue
        )
        val random = java.util.Random()

        for (i in 0 until features.length()) {
            val feature = features.getJSONObject(i)
            val geometry = feature.getJSONObject("geometry")
            val type = geometry.getString("type")
            
            if (type == "Polygon" || type == "MultiPolygon") {
                val coordinates = geometry.getJSONArray("coordinates")
                val polygons = mutableListOf<org.json.JSONArray>()
                
                if (type == "Polygon") {
                    polygons.add(coordinates)
                } else {
                    for (j in 0 until coordinates.length()) {
                        polygons.add(coordinates.getJSONArray(j))
                    }
                }
                
                for (polyCoords in polygons) {
                    for (ringIdx in 0 until polyCoords.length()) {
                        val ring = polyCoords.getJSONArray(ringIdx)
                        val geoPoints = ArrayList<GeoPoint>()
                        for (pointIdx in 0 until ring.length()) {
                            val point = ring.getJSONArray(pointIdx)
                            val lng = point.getDouble(0)
                            val lat = point.getDouble(1)
                            geoPoints.add(GeoPoint(lat, lng))
                        }
                        
                        val polygon = Polygon()
                        polygon.points = geoPoints
                        polygon.title = feature.getJSONObject("properties").optString("district", "Unknown")
                        
                        mapView.overlays.add(polygon)
                    }
                }
            }
        }
        mapView.invalidate()
    } catch (e: Exception) {
        e.printStackTrace()
    }
}

private fun getAdjustedRiskTier(districtName: String, crimeFilter: String, shiftFilter: String): String {
    val norm = districtName.lowercase().trim()
    var tier = "Moderate"

    if (norm.contains("bengaluru") || norm.contains("mysuru") || norm.contains("belagavi dist")) {
        tier = "Critical"
    } else if (norm.contains("mangalu") || norm.contains("hubli") || norm.contains("kalaburagi")) {
        tier = "High"
    } else if (norm.contains("bidar") || norm.contains("yadgir") || norm.contains("kodagu")) {
        tier = "Safe"
    }

    if (crimeFilter == "VIOLENT") {
        val criticalViolent = listOf("kalaburagi dist", "kalaburagi city", "ballari", "belagavi dist", "raichur", "vijayapura", "chitradurga")
        val highViolent = listOf("bengaluru city", "mysuru dist", "mysuru city", "mandya", "kolar", "shivamogga", "bagalkot")
        val modViolent = listOf("tumakuru", "hassan", "dharwad dist", "hubli-dharwad city", "chikkaballapura", "ramanagara")
        tier = if (criticalViolent.any { norm.contains(it) }) "Critical" else if (highViolent.any { norm.contains(it) }) "High" else if (modViolent.any { norm.contains(it) }) "Moderate" else "Safe"
    } else if (crimeFilter == "CYBER") {
        val criticalCyber = listOf("bengaluru city", "mysuru city", "hubli-dharwad city", "mangaluru city")
        val highCyber = listOf("bengaluru dist", "dakshina kannada", "udupi", "belagavi city")
        val modCyber = listOf("tumakuru", "kolar", "mandya", "shivamogga")
        tier = if (criticalCyber.any { norm.contains(it) }) "Critical" else if (highCyber.any { norm.contains(it) }) "High" else if (modCyber.any { norm.contains(it) }) "Moderate" else "Safe"
    } else if (crimeFilter == "NARCOTICS") {
        val criticalNarcotics = listOf("mangaluru city", "dakshina kannada", "udupi", "bengaluru city", "uttara kannada")
        val highNarcotics = listOf("belagavi city", "kodagu", "mysuru city", "hubli-dharwad city")
        val modNarcotics = listOf("shivamogga", "chikkamagaluru", "hassan", "belagavi dist")
        tier = if (criticalNarcotics.any { norm.contains(it) }) "Critical" else if (highNarcotics.any { norm.contains(it) }) "High" else if (modNarcotics.any { norm.contains(it) }) "Moderate" else "Safe"
    }

    if (shiftFilter == "NIGHT") {
        val isNightHotspot = norm.contains("city") || norm.contains("bengaluru") || norm.contains("mangaluru")
        if (isNightHotspot && tier == "High") tier = "Critical"
        else if (isNightHotspot && tier == "Moderate") tier = "High"
        else if (isNightHotspot && tier == "Safe") tier = "Moderate"
    }

    return tier
}
