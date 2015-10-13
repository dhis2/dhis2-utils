/*
 * A node js script which performs automated integrity checks against a
 * DHIS 2 server.
 *  
 * The script requires nodejs v0.11.13+ and depends on the urllib-sync 
 * library. NVM is convenient to use for installing the correct node version.
 * 
 * npm install urllib-sync
 * 
 * Define which nodejs version to use with:
 * 
 * nvm use v0.11.14
 * 
 * The flow of the script:
 * 
 * - Get integrity checks in the form of SQL views from server.
 * - Get the result of each SQL view. The SQL views should return no records, 
 *   and returned records are considered violations.
 * - Count number of violated views and records.
 * - Produce an integrity check summary.
 * - Write summary to file.
 * - Email the summary to server notifcation email using server Web API.
 * 
 * You will need to update configuration of the app structure, i.e. set
 * URL and authentication information.
 */

var urlsync = require('urllib-sync');
var fs = require('fs');

var app = {
	sqlViewsUrl: 'https://www.server.org/api/sqlViews.json?query=integrity_&fields=id,name,description&paging=false',
	sqlViewsBaseUrl: 'https://www.server.org/api/sqlViews',
	emailUrl: 'https://www.server.org/api/email/notification',
	options: {
		auth: 'sqlview:password',
		timeout: 40000
	},
	resultsFilename: 'output.tmp',
	encoding: 'utf8',
	results: {
		failed: [],
		successful: []
	},
	violatedChecks: 0,
	violatedRows: 0
};

app.sendEmail = function(text) {
	var email = {
		subject: 'Integrity check summary: ' + app.violatedChecks + ' failed checks out of ' + app.sqlViews.length + ' on ' + new Date().toString(),
		text: text
	};
	
	var postOptions = {
		auth: app.options.auth,
		timeout: 40000,
		data: JSON.stringify(email),
		headers: {
			'Content-Type': 'application/json'
		},
		method: 'post'
	};
	
	var response = urlsync.request(app.emailUrl, postOptions);
	
	if (response && 200 == response.status) {
		console.log('Email sent');
	}
	else {
		console.log('Email failed');
		console.log(response);
	}
}

app.run = function() {
	console.log('Getting integrity checks');
		
	var sqlViewResp = urlsync.request(app.sqlViewsUrl, app.options);
	var sqlViewJson = JSON.parse(sqlViewResp.data.toString(app.encoding));
	app.sqlViews = sqlViewJson.sqlViews;
	
	console.log('Running integrity checks');
	
	for (var i=0; i < app.sqlViews.length; i++) {
		var sqlView = app.sqlViews[i];
		var url = app.sqlViewsBaseUrl + '/' + sqlView.id + '/data.json';
		
		var response = urlsync.request(url, app.options);
		var data = response.data;
		var json = JSON.parse(data.toString(app.encoding));
		
		var result = {};
		result.description = sqlView.description;
		result.url = url;
		
		if (json.rows && json.rows.length > 0) {
			result.status = 'FAILED';
			result.violations = json.rows.length;
			app.violatedChecks++;
			app.violatedRows += json.rows.length;			
			app.results.failed.push(result);
		}
		else {
			result.status = 'SUCCESSFUL';
			app.results.successful.push(result);			
		}
		
		console.log('Got results for check: ' + sqlView.name + ', violations: '  + json.rows.length);
	}
		
	console.log('Writing integrity check results');
	
	var prettyResults = JSON.stringify(app.results, null, 2);
		
	fs.writeFile(app.resultsFilename, prettyResults, app.encoding);
	
	console.log('Summary');
	console.log('-------');
	console.log('Violated checks: ' + app.violatedChecks);
	console.log('Violated rows: ' + app.violatedRows);
	console.log('-------');
	
	console.log('Sending email');
	
	app.sendEmail(prettyResults);
	
	console.log('Integrity checks done');
}

app.run();
