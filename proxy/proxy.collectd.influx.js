
var http = require('http'),
    path = require('path'),
    home = require('home'),
    iniparser = require('iniparser');

console.log('Starting InfluxDB proxy for collectd');

try {
  var config = iniparser.parseSync(home.resolve('~/.config/home/home.cfg'));
} catch (err) {
  console.log('Error loading ~/.config/home/home.cfg: ', err);
  process.exit(1);
}

var influx_path = '/db/' + config.influxdb.influx_db + '/series?u=' + config.influxdb.influx_user + '&p=' + config.influxdb.influx_pass + '&time_precision=s';

if (config.collectd_proxy.collectd_proxy_verbose == 'true') {
  console.log(config);
  console.log('InfluxDB Path :', influx_path);
}

if (!config.collectd_proxy.collectd_proxy_port) {
  config.collectd_proxy.collectd_proxy_port = 8079;
}

if (!config.collectd_proxy.collectd_proxy_addr) {
  config.collectd_proxy.collectd_proxy_addr = '0.0.0.0';
}

var server = http.createServer(function(req, res) {
  var data = '';
  req.on('data', function(chunk) {
    data = data + chunk.toString();
  });
  req.on('end', function() {
    res.writeHead(200);
    res.end();

    var output = [];
    var parsed = JSON.parse(data);
    parsed.forEach(function(x) {
      var name = x.host + '.' + x.plugin;
      if (x.plugin_instance !== '') {
        name = name + '.' + x.plugin_instance;
      }
      name = name + '.' + x.type;
      if (x.type_instance !== '') {
        name = name + '.' + x.type_instance;
      }
      for(var z in x.dstypes) {
        if (x.dstypes[z] == 'counter' || x.dstypes[z] == 'gauge') {
          var n = name + '.' + x.dsnames[z];
          if (config.collectd_proxy.collectd_proxy_verbose == 'true') {
            console.log('Push metric', n);
          }
          output.push({
            name: n,
            columns: ['time', 'value'],
            points: [[x.time, x.values[z]]],
          });
        }
      }
    });
    var forwarded_req = {
      hostname: config.influxdb.influx_addr,
      port: config.influxdb.influx_port,
      path: influx_path,
      method: 'POST'
    };
    var r = http.request(forwarded_req, function(rr) {
      if (rr.statusCode != "200") {
        console.error('Request refused by influx db', rr.statusCode);
      }
    });

    r.on('error', function(e) {
      console.log('problem with request: ' + e.message);
    });
    r.write(JSON.stringify(output));
    r.end();
  });
});

server.listen(config.collectd_proxy.collectd_proxy_port, config.collectd_proxy.collectd_proxy_addr);

console.log('Proxy started on port', config.collectd_proxy.collectd_proxy_port, 'addr', config.collectd_proxy.collectd_proxy_addr);
