function getGraph(WORDNET, BASE_ID) {
    // Create a new directed graph
    var g = new dagreD3.graphlib.Graph().setGraph({}).setDefaultEdgeLabel(function(){return {};}),
        svg = d3.select("svg"),
        inner = svg.select("g");

    // Set up zoom support
    var zoom = d3.behavior.zoom().on("zoom", function() {
        inner.attr("transform", "translate(" + d3.event.translate + ")"
                              + "scale(" + d3.event.scale + ")");
    });
    svg.call(zoom);

    // Create the renderer
    var render = new dagreD3.render();
    
    var LIST = []
    
    var nodeToGraph = function(id) {
            node = WORDNET[id];
            
            html = '<div class="node-html">';
            html += '<div class="_name">' + node.names.join(', ') + '<span>' + node.no_images + ' (' + id + ')</span></div>';
            html += '<div class="_description">' + node.description + '</div>';
            if (node.images.length > 0) {
                html += '<div class="_images">';
                for (var i = 0; i < Math.min(5, node.images.length); i++) {
                    html += '<img src="' + node.images[i] + '" class="_image">';
                }
                html += '</div>';
            }
            
            g.setNode((id),{
                label: node.names[0],
                rx: 5,
                ry: 5,
                class: "_node_" + id + " node-generated" + (node.selected ? " _selected-node" : "") + (node.visited ? " _visited-node" : "") + (node.deleted ? " _deleted-node" : "")  + (node.children.length == 0 ? " _child-node" : "")  + (node.no_images >= 500 ? " _image-node" : "")
            });
            
            WORDNET[id].shown = true;
            
            LIST.push([id, html]);
        },
        nodeFromGraph = function(id) {
            g.removeNode(id);
        },
        showNode = function(id) {
            if (WORDNET[id].shown) return;
            
            nodeToGraph(id);
            
            node.parents.forEach(function(parent_id) {
                if (WORDNET[parent_id].shown) {
                    g.setEdge(parent_id, id);
                }
            });
            if (WORDNET[id].expanded || WORDNET[id].children.length == 1) expandNode(id);
        },
        expandNode = function(id, ctrlKey = false) {
            if (!WORDNET[id].shown) return;
            
            WORDNET[id].children.forEach(function(child_id) {
                if (WORDNET[child_id].shown) {
                    g.setEdge(id, child_id);
                } else {
                    showNode(child_id);
                    if (WORDNET[child_id].expanded || ctrlKey) {
                        expandNode(child_id, ctrlKey);
                    }
                }
            });
            WORDNET[id].expanded = true;
        },
        hideChildren = function(id) {
            WORDNET[id].children.forEach(function(child_id) {
                if (WORDNET[id].shown) {
                    g.removeEdge(id, child_id);
                    hideChildren(child_id);
                    nodeFromGraph(child_id);
                    
                    WORDNET[child_id].shown = false;
                }
            });
            
        },
        closeNode = function(id) {
            if (!WORDNET[id].shown || !WORDNET[id].expanded) return;
            
            hideChildren(id);
            
            WORDNET[id].expanded = false;
        };
    
    
    nodeToGraph(BASE_ID);
    
    var myRender = function() {
        render(inner, g);
        
        LIST.forEach(function(x) {
            var id = x[0], html = x[1];
                        
            g.node(id).elem.addEventListener("click", function(event) {
                if (WORDNET[id].expanded) {
                    closeNode(id);
                } else {                    
                    expandNode(id, event.ctrlKey);
                }
                myRender();
            });
            g.node(id).elem.addEventListener("contextmenu", function(event) {
                event.preventDefault();
                
                target = document.querySelector('._node_'+id);

                if (event.ctrlKey) {
                    voteOne(target, id, 'visit', !target.classList.contains("_visited-node"));
                } else if (event.altKey) {
                    voteOne(target, id, 'delete', !target.classList.contains("_deleted-node"));
                } else {
                    voteOne(target, id, 'select', !target.classList.contains("_selected-node"));
                }
            });
            $('._node_' + id).attr("title", html).tipsy({ gravity: "w", opacity: 1, html: true });

        });
        
        LIST = [];
    }
    
    myRender();
 
    var utils = {
            graphWidth: function() { return g.graph().width + 40; },
            graphHeight: function() { return g.graph().height + 40; },
            svgWidth: function() { return parseInt(svg.style("width").replace(/px/, "")); },
            svgHeight: function() { return parseInt(svg.style("height").replace(/px/, "")); },
        },
        zooming = (function() {
            var currentScale = 1,
                scale = function() { return Math.min(utils.svgWidth() / utils.graphWidth(), utils.svgHeight() / utils.graphHeight()); },
                zoom_out_map = function(initialize) {
                    var _scale = scale(),
                        translate = [
                            (utils.svgWidth() - utils.graphWidth() * _scale) / 2 + 20,
                            (utils.svgHeight() - utils.graphHeight() * _scale) / 2 + 20
                        ];
                    
                    _scale = _scale < 3 ? _scale : 3;
                    zoom.translate(translate).scale(_scale).event(initialize === true ? svg : svg.transition().duration(500));
                    
                    currentScale = _scale;
                }
            
            zoom_out_map(true);
            
            return {
                scale: scale,
                zoom_out_map: zoom_out_map,
                zoom_out: function() {
                    currentScale *= 0.75;
                    zoom.scale(currentScale).event(svg.transition().duration(500));
                },
                zoom_in: function() {
                    currentScale *= 1.25;
                    zoom.scale(currentScale).event(svg.transition().duration(500));
                }
            }
        })(),
        registerControls = function() {
            document.querySelector("#controls .zoom_in").addEventListener("click", zooming.zoom_in, false);
            document.querySelector("#controls .zoom_out").addEventListener("click", zooming.zoom_out, false);
            document.querySelector("#controls .zoom_out_map").addEventListener("click", zooming.zoom_out_map, false);
        };
    
    registerControls();
    
    return {
        graph: g
    };
}

function voteOne(el, id, type, value) {
	switch(type) {
		case 'select':
			WORDNET[id].selected = value;
			addOrRemoveClass(id, "_selected-node", value, el);
			break;
		case 'visit':
			WORDNET[id].visited = value;
			addOrRemoveClass(id, "_visited-node", value, el);
			break;
		case 'delete':
			WORDNET[id].deleted = value;
			addOrRemoveClass(id, "_deleted-node", value, el);
			break;
		default:
			console.error(response);
			break;
	}
}

function addOrRemoveClass(id, cls, add, el) {
    classes = G.graph.node(id).class.split(' ');
    if (add) {
        G.graph.node(id).class += ' ' + cls;
        el.classList.add(cls);
    }
    else {
        classes.splice(classes.indexOf(cls), 1);
        G.graph.node(id).class = classes.join(' ');
        el.classList.remove(cls);
    }
}

function saveToFile() {
	keys = ""
	for(var key in WORDNET) {
		if (WORDNET[key].selected)
			keys += key + "\n";
	}
	console.log(keys);
}
