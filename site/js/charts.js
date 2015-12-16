String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
}

function generateBarChart(data) {

	var columns = ['data1'].concat(data.values);
	var chart = c3.generate({
		 size: {
		        height: 600
		    },
		padding: {
			left: 110,
		},
		bindto : data.element,
		data : {
			columns : [columns],
			type : 'bar',
			colors : { data1 : data.color}
		},
		axis : {
			x : {
				type : 'category',
				categories : data.categories
			},
			y : {
				tick: {
					format: function (x) { return isInt(x)? x : "";}
				}
			},
			rotated : true,
		},
		legend : {
			show : false
		}
	});

	chart.data.names({data1: data.label});
}

function isInt(n) {
	return n % 1 === 0;
}

function removeSpecialCharacters(text) {
	text = text.replace(/[á|ã|â|à]/gi, "a");
	text = text.replace(/[é|ê|è]/gi, "e");
	text = text.replace(/[í|ì|î]/gi, "i");
	text = text.replace(/[õ|ò|ó|ô]/gi, "o");
	text = text.replace(/[ú|ù|û]/gi, "u");
	text = text.replace(/[ç]/gi, "c");
	text = text.replace(/[ñ]/gi, "n");
	text = text.replace(/[á|ã|â]/gi, "a");

	text = text.replace(/\W/gi, ".");
	text = text.replace(/(\-)\1+/gi, ".");
	return text;
}

function findDistrict(dist_array, elem) {
	for (var i = 0; i < dist_array.length; i++) {
		if (dist_array[i].clean_dist_name == elem) 
			return i;
	}
	return -1;
}

function districtComparator(a, b) {
	return b.faltas_count - a.faltas_count;
}

function processFaltaPerDisctrict() {
	var falta_per_district = [];

	for (var i = 0; i < notifications.length; i++) {
		var district_name = notifications[i]['district'];

		if (district_name == "") continue;

		var clean_dist_name = removeSpecialCharacters(district_name.trim().toLowerCase());
		var index_of_district = findDistrict(falta_per_district, clean_dist_name);

		if (index_of_district == -1) {
			var district = {};
			district.name = district_name;
			district.clean_dist_name = clean_dist_name;
			district.faltas_count = 1;
			falta_per_district.push(district);
		} else {
			falta_per_district[index_of_district].faltas_count += 1;
		}
	}

	falta_per_district.sort(districtComparator);

	var falta_values = [];
	var district_names = [];

	for (var i = 0; i < falta_per_district.length; i++) {
		var district = falta_per_district[i];
		falta_values.push(district.faltas_count);
		district_names.push(district.name.capitalize());
	}

	return {
		'element' : '#falta-per-district-chart',
		'label' : 'Número de faltas de água',
		'values' : falta_values,
		'categories' : district_names,
		'color' : '#ff4040'
	};
}

function loadResults() {
	var falta_per_district_data = processFaltaPerDisctrict();
	generateBarChart(falta_per_district_data);
}