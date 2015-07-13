var counter = 0;
var ip_table_html;
$(function () {
    ip_table_html = document.getElementById("ip-table[0]").innerHTML;
    counter++;
});

function submitForm() {
    var all_tables = document.getElementById("ff").getElementsByTagName("table");
    for (var i = 0; i < all_tables.length; i++) {
        var ip = all_tables[i].getElementsByTagName("input")[1];
        ip.setAttribute("name", "HostName[" + i + "]");
        var host = all_tables[i].getElementsByTagName("input")[4];
        host.setAttribute("name", "IP[" + i + "]");
    }
    document.getElementsByName("count")[0].value = all_tables.length;
    document.getElementById("ff").submit();
}
function addForm() {
    // Add new element
    var new_elem = document.createElement("table");
    new_elem.innerHTML = ip_table_html;
    var append_form = document.getElementById("ff");
    append_form.appendChild(new_elem);

    new_elem.setAttribute("id", "ip-table[" + counter + "]");

    var new_td_button = new_elem.getElementsByClassName("easyui-linkbutton");
    new_td_button[0].setAttribute("onclick", "destroyElement(" + counter + ")");
    counter++;
}
function destroyElement(i) {
    var removeNode = document.getElementById("ip-table[" + i + "]");
    removeNode.remove();
}

function checkValidity(type, my_id, value){
    var input_is_valid = false;
    if(type === 'HostName'){
        var all_tables = document.getElementById("ff").getElementsByTagName("table");
        for (var i = 0; i < all_tables.length; i++){
            if(i === my_id) continue;
        }

        $.ajax({
            url: "check_input_validity/",
            success: function(result){
                if(result === 'False')
                    return "HostName already exists in database."
            }
        })
    }
    else if (type === 'IP'){

    }
}