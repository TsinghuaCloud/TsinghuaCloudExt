var canvas = document.getElementById('canvas');
var graph = new Q.Graph(canvas);
var old_result = "";

action = function(){
    $('#monitor-table').datagrid({
        url:'scheduledatatable/'
    });
};
setInterval("action()", 3000);
setInterval("tenants()", 3000);

$(function () {
    action();
    tenants();
});

function createText(name, x, y, fontSize, color, parent) {
    var text = graph.createText(name, x, y);
    text.setStyle(Q.Styles.LABEL_ANCHOR_POSITION, Q.Position.CENTER_MIDDLE);
    text.setStyle(Q.Styles.LABEL_POSITION, Q.Position.CENTER_MIDDLE);
    text.setStyle(Q.Styles.LABEL_FONT_SIZE, fontSize);
    text.setStyle(Q.Styles.LABEL_COLOR, color);
    text.setStyle(Q.Styles.LABEL_BACKGROUND_COLOR, null);
    if (parent) {
        parent.addChild(text);
    }
    return text;
}

graph_init = function() {
    graph.clear();
    createText("监控实例图", -100, -200, 20, "#F00");
    createText("图例", 250, -200, 15, "#00");
    var cloudmodel = graph.createNode("监控服务器", 250, -110);
    cloudmodel.setStyle(Q.Styles.LABEL_POSITION, Q.Position.RIGHT_MIDDLE);
    cloudmodel.setStyle(Q.Styles.LABEL_OFFSET_X, 30);
    cloudmodel.size = {width: 50};
    cloudmodel.image = STATIC_URL + "img/server.jpg";
    var servermodel = graph.createNode("监控节点", 250, -50);
    servermodel.setStyle(Q.Styles.LABEL_POSITION, Q.Position.RIGHT_MIDDLE);
    servermodel.setStyle(Q.Styles.LABEL_OFFSET_X, 30);
    servermodel.image = "Q-server";
    var clientmodel = graph.createNode("被监控节点", 250, 0);
    clientmodel.setStyle(Q.Styles.LABEL_POSITION, Q.Position.RIGHT_MIDDLE);
    clientmodel.setStyle(Q.Styles.LABEL_OFFSET_X, 30);
};

tenants = function () {
    $.ajax({
        url: 'scheduledata/',
        success: function (result) {
            if(JSON.stringify(result) != JSON.stringify(old_result)) {
                old_result = result;
                graph_init();
                var mainNode = graph.createNode("监控服务器", -150, -110);
                mainNode.size = {width: 50};
                mainNode.image = STATIC_URL + "img/server.jpg";
                var len = result.length;
                var cur_left = -350;
                var server = [];
                for (var k = 0; k < len; k++) {
                    server[k] = graph.createNode(result[k]['ServerName'], -200 + 150 * k, -10);
                    server[k].size = 20;
                    server[k].image = "Q-server";
                    graph.createEdge(mainNode, server[k]);
                    var host = [];
                    for (var i = 0; i < result[k]['Host'].length; i++) {
                        host[i] = graph.createNode(result[k]['Host'][i]['HostName'], cur_left, 80);
                        host[i].url = '/hostdetail/' + result[k]['Host'][i]['HostId'];
                        host[i].clickable = true;
                        cur_left += 100;
                        graph.createEdge(server[k], host[i]);
                    }
                }
            }
        }
    })
};

graph.addCustomInteraction({
    onclick: function (evt, graph) {
        Q.log("click");
        var ui = graph.getUIByMouseEvent(evt);
        if (ui && ui.data.clickable) {
             window.location.href = ui.data.url;
        }
    }
});