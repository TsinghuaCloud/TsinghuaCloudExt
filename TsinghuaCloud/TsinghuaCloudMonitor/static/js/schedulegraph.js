var graph = new Q.Graph(canvas);

graph.styles = {};
graph.styles[Q.Styles.ARROW_TO_STYLES] = {
    lineWidth: 1,
    lineJoin: "round"//"miter"
};

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

var VPNFlexEdgeUI = function (edge, graph) {
    Q.doSuperConstructor(this, VPNFlexEdgeUI, arguments);
}
VPNFlexEdgeUI.prototype = {
    drawEdge: function (path, fromUI, toUI, edgeType, fromBounds, toBounds) {
        var from = fromBounds.center;
    }
}

Q.extend(VPNFlexEdgeUI, Q.EdgeUI);

createText("监控实例图", 200, 150, 20, "#F00");
var model = graph.graphModel;

tenants = function () {
    $.ajax({
        url: 'scheduledata/',
        success: function (result) {
            var mainNode = graph.createNode("主机", 0, -110);
            var len = result.length;
            console.info(result);
            var cur_left = -200;
            var cur_height = -110;
            var server = [];
            //console.info(result['projects'][0].name);
            for (var k = 0; k < len; k++) {
                server[k] = graph.createNode(result[k]['ServerName'], -50 + 100 * k, -10);
                graph.createEdge(mainNode, server[k]);
                var host = [];
                for (var i = 0; i < result[k]['Host'].length; i++){
                    host[i] = graph.createNode(result[k]['Host'][i], cur_left, 80);
                    cur_left += 100;
                    graph.createEdge(server[k], host[i]);
                }
            }

        }
    });
};

var setSelectionStyle = function (element) {
    if (!(element instanceof Q.Node)) {
        return;
    }
    var selected = graph.isSelected(element);
    if (selected) {
        //directSubmap(element);
        //console.info(element);
        if (element.toString().length > 20) {
            directSubmap(element.toString());
            //alert('dddss');
        }
    } else {
        element.setStyle(Q.Styles.RENDER_COLOR, null);
        element.setStyle(Q.Styles.PADDING, 0);
        element.setStyle(Q.Styles.BORDER, 0);
    }
}
graph.selectionChangeDispatcher.addListener(function (evt) {
    if (window.onselectionchange) {
        window.onselectionchange(evt, graph);
    }
    var data = evt.data;
    if (!data) {
        return;
    }
    if (Q.isArray(data)) {
        for (var i = 0, l = data.length; i < l; i++) {
            setSelectionStyle(data[i]);
        }
    } else {
        setSelectionStyle(data);
    }
});
tenants();

