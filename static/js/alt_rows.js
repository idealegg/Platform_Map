/**
 * Created by huangd on 2019/9/10.
 */
    function altRows(){
            var tables = document.getElementsByClassName('altrowstable');
            for (var j = 0; j < tables.length; ++j) {
                var rows = tables[j].getElementsByTagName("tr");
                //console.log(rows.length);
                for (var i = 0; i < rows.length; i++) {
                    if (i % 2 == 0) {
                        rows[i].style.backgroundColor = '#ffffff';
                    } else {
                        rows[i].style.backgroundColor = '#efefef';
                    }
                }

                var values = tables[j].getElementsByClassName('itemvalue');
                for (i = 0; i < values.length; i++) {
                    if ((values[i].innerHTML == 'N') || (values[i].innerHTML == 'n') || (values[i].innerHTML == 'unknown')
                        || (values[i].innerHTML == 'Unknown') || (values[i].innerHTML == 'UNKNOWN')) {
                        values[i].style.color = '#ff0000';
                    }
                }

                var valids = document.getElementsByClassName('validity');
                for (i = 0; i < valids.length; i++) {
                    checkValidity(valids[i]);
                }
            }
    }

    function altRow(t){
      //console.log('altRow');
      //console.log(t.id);
      if(t.id % 2 == 0){
        t.style.backgroundColor='#ffffff';
      }else{
        t.style.backgroundColor='#efefef';
      }
    }


function toggleWikiNode(icon) {
    var
        $i = $(icon),
        $div = $i.parent(),
        expand = $div.attr('expand');
    if (expand === 'true') {
        $div.attr('expand', 'false');
        $i.removeClass('uk-icon-minus-square-o');
        $i.addClass('uk-icon-plus-square-o');
        $div.find('>div').hide();
    } else {
        $div.attr('expand', 'true');
        $i.removeClass('uk-icon-plus-square-o');
        $i.addClass('uk-icon-minus-square-o');
        $div.find('>div').show();
    }
}

function collapseWikiNode(icons, rec) {
    for (var j=0; j<icons.length; ++j) {
        var
                $i = $(icons.get(j)),
                $div = $i.parent();
        $div.attr('expand', 'false');
        $i.removeClass('uk-icon-minus-square-o');
        $i.addClass('uk-icon-plus-square-o');
        $div.find('>div').hide();
        if (rec) {
            $div.find('>div>i').each(function () {
                collapseWikiNode(this, rec);
            });
        }
    }
}

function expandWikiNode(icons, rec) {
    for (var j=0; j<icons.length; ++j) {
        var
                $i = $(icons.get(j)),
                $div = $i.parent();
        $div.attr('expand', 'true');
        $i.removeClass('uk-icon-plus-square-o');
        $i.addClass('uk-icon-minus-square-o');
        $div.find('>div').show();
        if (rec) {
            $div.find('>div>i').each(function () {
                expandWikiNode(this, rec);
            });
        }
    }
}

    function onClickItem(t, item) {
      //console.log('onClickItem');
      var form = document.createElement('form');
      form.action = '#';
      form.method = 'post';
      var input = document.createElement('input');
      input.type = 'hidden';
      input.name = item;
      input.value = t.innerHTML;
      form.appendChild(input);
      document.body.append(form);
      form.submit();
    }

    function checkValidity(t) {
          //console.log('checkValidity')
          //console.log(t);
          var date = t.getElementsByTagName('input')[0];
          var sp = t.getElementsByTagName('span')[0];
          var i_Date = Date.parse(date.value);
          var c_Date = Date.parse(new Date());
          if (i_Date + 86400000 <= c_Date){
            sp.className = 'uk-icon-close';
          }
          else{
            sp.className = 'uk-icon-check';
          }
    }

    function onClickSelectDate(t, t2) {
        //console.log(t);
        //console.log(t2);
      WdatePicker({
          el: t, //点击对象id，一般可省略el
          lang: 'en', //语言选择，一般用auto
          dateFmt: 'yyyy-MM-dd', //时间显示格式，年月日 时分秒，年月日就是yyyy-MM-dd
          //minDate: '#F{$dp.$D(\'inputstarttime\')}', //最小日期
         // maxDate: '%y-%M-%d', //最大日期（当前时间）
          readOnly: false, //是否只读
          isShowClear: true, //是否显示“清空”按钮
          isShowOK: true, //是否显示“确定”按钮
          isShowToday: true, //是否显示“今天”按钮
          autoPickDate: true, //为false时 点日期的时候不自动输入,而是要通过确定才能输入，为true时 即点击日期即可返回日期值，为null时(推荐使用) 如果有时间置为false 否则置为true
          autoUpdateOnChanged: checkValidity(t2)
      })
    }

    function submit_platform(site, pf, b) {
        //console.log('submit_platform');
        var $b1 = $(b),
            $err = $b1.next(),
            $div = $b1.parent().parent(),
            $inputs = $div.find('>div>input'),
            $valid =  $inputs.get(2).value;

        //console.log($err);
        if ($valid != "") {
            //console.log($valid);
            var date = new Date(Date.parse($valid));
            //console.log(date);
            $valid = date.getFullYear() + '-' + (date.getMonth() + 1) + '-' + date.getDate();
        }
        $err.text('Submitting...');
        $err.css('color', '#e28327');
        var jqxhr = $.ajax({
            url: '/submit_platform/',
            async: true,
            data:
            {
            site: site,
            pf: pf,
            desc: $inputs.get(0).value,
            owner: $inputs.get(1).value,
            valid: $valid,
            last_mod: $('#last-modified-'+site+'-'+pf).val()},
            type: "POST",
            dataType: 'json',
            beforeSend: function () {
                console.log('beforeSend');
                $b1.attr('disabled', true);
            },
            success: function (res) {
                //console.log('success');
                //console.log(res);
                $err.text(res['ret']);
               // $b1.attr('disabled', false);
                if(res['ret'] === 'Successful'){
                    $('#last-modified-'+site+'-'+pf).val(res['last_mod']);
                    $err.css('color', '#00ff00');
                }else{
                    $err.css('color', '#ff0000');
                }
            },
            complete: function () {
                console.log('complete');
                $b1.attr('disabled', false);
            },
            error: function () {
                //console.log('error');
                $err.text('Failed');
                $err.css('color', '#ff0000');
            }
        });

    }

    function dbclick_tty_nodes(t) {
        function get_all_nodes(txt) {
            var ns = txt.split(' ').filter(function(x){return x!=''});
            var nodes = new Array();
            for(var n_i=0; n_i < ns.length; n_i++){
                var $n_e = $('#last-modified-'+ns[n_i]);
                if ($n_e.length){
                     nodes.push({'n': ns[n_i], 't': $n_e.val()});
                }
            }
            //console.log('nodes: '+nodes);
            return JSON.stringify(nodes);
        }
        if ($(t).children("input").length > 0) {
            return false;
        }
        //console.log('host:');
        var $pp = $(t).parents('.tty_info');
        var tty = $pp.find('.tty_text').text();
        var $pppp = $(t).parents('.column_item');
        var host = $pppp.find('.dm_host').text();
        var $err = $pppp.find('#error_message');
        //console.log(host);
        //console.log(tty);
        var tdDom = $(t);
        //保存初始值
        var tdPreText = $(t).text();
        var width = $(t).width();
        var roll_back = false;
        var node_inf = null;
        //var padding = $(t).css('padding-left');
        //给td设置宽度和给input设置宽度并赋值
        $(t).html("<input type='text'>").find("input").width(width).val(tdPreText.trim()).focus();
        //失去焦点的时候重新赋值
        var inputDom = $(t).find("input");
        inputDom.blur(function () {
            var newText = $(this).val();
            if (newText.trim() === tdPreText.trim()){
                $err.text('No change');
                $err.css('color', '#e28327');
                roll_back = true;
            }else if(newText.trim() === ''){
                $err.text('Not allowed to remove!');
                $err.css('color', '#ff0000');
                roll_back = true;
            }
            else {

                var jqxhr = $.ajax({
                    url: '/submit_display/',
                    //url: '/submit1212_display/',
                    async: true,
                    data: {
                        host: host,
                        ns: newText,
                        tty: tty,
                        n_time: get_all_nodes(newText)
                    },
                    dataType: 'json',
                    type: "POST",
                    beforeSend: function () {
                        console.log('beforeSend');
                        $(t).parent().css('outline', 'outset');
                        $err.text('Submitting...');
                        $err.css('color', '#e28327');
                    },
                    success: function (res) {
                        console.log('success');
                        //console.log(res);
                        $err.text(res['ret']);
                       // $b1.attr('disabled', false);
                        if (res['ret'] != 'Successful'){
                            tdDom.text(tdPreText);
                            tdDom.attr('title', tdPreText);
                            $err.css('color', '#ff0000');
                        }else {
                            $err.css('color', '#00ff00');
                            if (res['cx'].length > 0 ){
                                for(var i = 0;i < res['cx'].length;++i ){
                                    var cx = res['cx'][i];
                                    var $h = $(document).find('#div-'+cx['host']);
                                    var $tty_info = $h.find('.tty_text').filter(
                                        function(x) {
                                            return $(this).text() === 'TTY'+cx['tty'];
                                        }).parent();
                                    $tty_info.attr('conflict', cx['c']);
                                    if (cx['ns'] === ''){
                                        node_inf = $tty_info.find('.node_text');
                                        node_inf.html('&nbsp;');
                                        node_inf.attr('title', '');
                                    }else{
                                        node_inf = $tty_info.find('.node_text');
                                        node_inf.text(cx['ns']);
                                        node_inf.attr('title', cx['ns']);
                                        $tty_info.find('input').remove();
                                        for(var t_i=0;t_i<cx['n_time'].length;t_i++){
                                            node_inf.after('<input type="hidden" id="last-modified-'
                                            +cx['n_time'][t_i]['n']
                                            +'" value="'
                                            +cx['n_time'][t_i]['t']
                                            +'" />');
                                        }
                                    }
                                }
                            }
                        }
                    },
                    complete: function () {
                        console.log('complete');
                        $(t).parent().css('outline-style', 'none');
                    },
                    error: function (req, errmsg, exception) {
                        console.log('error');
                        console.log('errmsg'+errmsg);
                        console.log('exception'+exception);
                        $err.css('color', '#ff0000');
                        if (errmsg){
                            $err.text(errmsg);
                        }else{
                            $err.text('Failed');
                        }
                        tdDom.text(tdPreText);
                        tdDom.attr('title', tdPreText);
                    }
                });
            }
            $(this).remove();
            if (roll_back){
                tdDom.text(tdPreText);
            }else{
                tdDom.text(newText);
                tdDom.attr('title', newText);
            }
        });
    }

    function altBackendRow() {
        console.log(altBackendRow);
        var $tbody = $('tbody');
        var $td = $tbody.find('td').filter(function(x) {
                                        return $(this).text() === 'Collecting';
                                    });
        if($td){
            var $tr = $td.parent();
            $tr.css('background-color', '#ff0000');
        }
    }

    function closeConn() {
        if(window.s) {
            window.s.close();
            $("#real_time_state").text('closed');
            window.s = null;
        }
    }

    function onclickwebsocketbtn(){
        console.log("onclickwebsocketbtn");
        var btn = $("#start_real_time");
        var state = $("#real_time_state");
        if (window.s){
            closeConn();
            window.s = null;
            btn.text("Start Real Time Monitor");
            return;
        }

        if(typeof(WebSocket) == "undefined") {
            state.text("Not support!");
            return;
        }
        btn.attr('disabled', true);
        //var socket = new WebSocket("ws://127.0.0.1:8000/client_connect/");
        var socket = new WebSocket("ws://"+location.host+"/client_connect/");
        window.s = socket;
        socket.onopen = function () {
            /* 与服务器端连接成功后，自动执行 */
            state.text("Successful!");
            socket.send($("#req_time").val());
            btn.text("Stop Real Time Monitor");
            btn.attr('disabled', false);
        };
        socket.onmessage = function (event) {
            /* 服务器端向客户端发送数据时，自动执行 */
            console.log(event);
            var r = JSON.parse(event.data);
            var to_del = new Array();
            var insert_at_first = false;
            var c_tr = null;

            for(var i = 0; i < r.length; ++i){
                var t_tr = $("#tr-"+r[i]['Site']+"-"+r[i]['Platform']);
                if(t_tr.length){
                    t_tr.attr('id', "tr-"+r[i]['Site']+"-"+r[i]['Platform']+'-2');
                    to_del.push(t_tr);
                }
                var to_insert = '<tr id="tr-'+r[i]['Site']+'-'+r[i]['Platform']+'">'+
                          "<td class='itemvalue'>"+r[i]['Site']+"</td>"+
                          "<td class='itemvalue'>"+r[i]['Platform']+"</td>"+
                          "<td class='itemvalue'>"+r[i]['Begin']+"</td>"+
                          "<td class='itemvalue'>"+r[i]['End']+"</td>"+
                          "<td class='itemvalue'>"+r[i]['State']+"</td>"+
                          "<td class='itemvalue'>"+r[i]['Counter']+"</td></tr>";
                if ($('tbody>tr').length) {
                    var max_counter = 0;
                    $('tbody>tr').each(
                        function(){
                            if($(this).children('td').eq(5).text() > max_counter){
                                max_counter = parseInt($(this).children('td').eq(5).text());
                            }});
                    insert_at_first = max_counter < r[r.length - 1]['Counter'];
                }else{
                    insert_at_first = true;
                }

                if(insert_at_first){
                    console.log('insert at first!');
                    $('tbody').prepend(to_insert);
                    c_tr = $('tbody>tr').first();
                    insert_at_first = false;
                }else{
                    var max_begin = '';
                    $('tbody>tr').each(
                        function(){
                            if($(this).children('td').eq(2).text() >= max_begin){
                                max_begin = $(this).children('td').eq(2).text();
                                c_tr = $(this);
                            }});
                    console.log('insert after current tr!');
                    c_tr.after(to_insert);
                }
            }
            to_del.forEach(function (x) {
                x.remove();
            });
            //c_tr.css('background-color', '#ff0000');
            state.text('updated');
            altBackendRow();
        };
        socket.onclose = function (event) {
            /* 服务器端主动断开连接时，自动执行 */
            state.text('Closed or limit reached!');
            btn.text("Start Real Time Monitor");
            window.s = null;
        };


    }