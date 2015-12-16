var map, heatmap;
var markers = [];
var lat_lng_array = [];
var notifications = [];

var DEFAULT_MARKER_ICON = "img/aguanossa-marker.png";
var UPDATE_INTERVAL = 300000;

function initialize() {
	googleMapsInit();
	loadNotifications();
    console.log("test");
	setInterval(loadNotifications, UPDATE_INTERVAL);
}

function googleMapsInit() {
	var mapOptions = {
			zoom : 13,
			center : new google.maps.LatLng(-7.220, -35.886) //	centro de campina grande
	};

	map = new google.maps.Map(document.getElementById('map-canvas'),
			mapOptions);
	
	var showHeatMap = document.createElement('div');
	var homeControl = new HeatMapControl(showHeatMap, map);
	var showCircleMap = document.createElement('div');
	var circleControl = new CircleMapControl(showCircleMap, map);

	showHeatMap.index = 1;
	showCircleMap.index = 1;

	map.controls[google.maps.ControlPosition.TOP_RIGHT].push(showCircleMap);
	map.controls[google.maps.ControlPosition.TOP_RIGHT].push(showHeatMap);
}

function HeatMapControl(controlDiv, map) {
	// Set CSS styles for the DIV containing the control
	// Setting padding to 5 px will offset the control
	// from the edge of the map
	controlDiv.style.padding = '4px';

	// Set CSS for the control border
	var controlUI = document.createElement('div');
	controlUI.style.backgroundColor = 'white';
	controlUI.style.borderStyle = 'solid';
	controlUI.style.borderWidth = '1px';
	controlUI.style.cursor = 'pointer';
	controlUI.style.textAlign = 'center';
	controlUI.title = 'Clique para mostrar o mapa de intensidade';
	controlDiv.appendChild(controlUI);

	// Set CSS for the control interior
	var controlText = document.createElement('div');
	controlText.style.fontFamily = 'questrialRegular';
	controlText.style.fontSize = '15px';
	controlText.style.paddingLeft = '5px';
	controlText.style.paddingRight = '5px';
	controlText.innerHTML = '<b>Mapa de Intensidade</b>';
	controlUI.appendChild(controlText);

	// Setup the click event listeners: simply set the map to
	// Chicago
	google.maps.event.addDomListener(controlUI, 'click', function() {
		toggleHeatmap();
	});
}

function CircleMapControl(controlDiv, map) {
	// Set CSS styles for the DIV containing the control
	// Setting padding to 5 px will offset the control
	// from the edge of the map
	controlDiv.style.padding = '4px';

	// Set CSS for the control border
	var controlUI = document.createElement('div');
	controlUI.style.backgroundColor = 'white';
	controlUI.style.borderStyle = 'solid';
	controlUI.style.borderWidth = '1px';
	controlUI.style.cursor = 'pointer';
	controlUI.style.textAlign = 'center';
	controlUI.title = 'Clique para mostrar o mapa de círculos gradientes';
	controlDiv.appendChild(controlUI);

	// Set CSS for the control interior
	var controlText = document.createElement('div');
	controlText.style.fontFamily = 'questrialRegular';
	controlText.style.fontSize = '15px';
	controlText.style.paddingLeft = '5px';
	controlText.style.paddingRight = '5px';
	controlText.innerHTML = '<b>Mapa de Círculos</b>';
	controlUI.appendChild(controlText);

	// Setup the click event listeners: simply set the map to
	// Chicago
	google.maps.event.addDomListener(controlUI, 'click', function() {
		toggleCirclemap();
	});
}

function loadNotifications() {
	$.ajax({
		url : '/aguanossa-backend/get_notifications',
		success : function(data) {
			deleteMarkers();
			notifications = $.parseJSON(data);

			lat_lng_array = [];

			for (var i = 0; i < notifications.length; i++) {
				var notification = notifications[i];
				if (notification.lat_lng == "") {
					continue;
				}
				lat_lng_array.push(processLatAndLng(notification.lat_lng));
			}

			var pointArray = new google.maps.MVCArray(lat_lng_array);

			heatmap = new google.maps.visualization.HeatmapLayer({
				data: pointArray,
				radius: 30
			});

			placeDefaultMarkers();
			$("#notification-counter").text(lat_lng_array.length);
		}
	});
}

function toggleHeatmap() {
	if (heatmap.getMap() == null){
		deleteMarkers();
		heatmap.setMap(map);
	} else {
		heatmap.setMap(null);
		placeDefaultMarkers();
	}
}

function toggleCirclemap() {
	heatmap.setMap(null);
	if (markers.length != 0 && markers[0].type == "circle"){
		deleteMarkers();
		placeDefaultMarkers();
	} else {
		deleteMarkers();
		placeCircles();
	}
}

function processLatAndLng(stringLatAndLng) {
	var lat_lng = stringLatAndLng.split("/");
	var lat = parseFloat(lat_lng[0].trim());
	var lng = parseFloat(lat_lng[1].trim());
	return new google.maps.LatLng(lat, lng);
}

function placeDefaultMarkers() {
	for (var i = 0; i < lat_lng_array.length; i++) {
		markers.push(placeDefaultMarker(lat_lng_array[i]));	
	}
}

function placeCircles() {
	for (var i = 0; i < lat_lng_array.length; i++) {
		markers.push(placeCircle(lat_lng_array[i]));	
	}
}

function placeDefaultMarker(location) {
	var marker = new google.maps.Marker({
		position : location,
		draggable : false,
		map : map,
		//animation: google.maps.Animation.DROP,
		icon : DEFAULT_MARKER_ICON,
		//title : "Hello World!"
		type: "default"
	});
	return marker;
}

function placeCircle(location) {
	var circulo = {
			strokeColor: '#d39b07',
			strokeOpacity: 0.8,
			strokeWeight: 1.2,
			fillColor: '#d39b07',
			fillOpacity: 0.2,
			map: map,
			center: location,
			radius: 125,
			type: "circle"
	};
	return new google.maps.Circle(circulo);
}

function setAllMap(map) {
	for (var i = 0; i < markers.length; i++) {
		markers[i].setMap(map);
	}
}

function clearMarkers() {
	setAllMap(null);
}

function deleteMarkers() {
	clearMarkers();
	markers = [];
}

google.maps.event.addDomListener(window, 'load', initialize);