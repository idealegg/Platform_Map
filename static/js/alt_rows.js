/**
 * Created by huangd on 2019/9/10.
 */
    $(function () {
        var $gotoTop = $('div.x-goto-top');
        var onScroll = function () {
            var wtop = $('.right_content').scrollTop();
            //console.log('wtop: '+wtop);
            if (wtop > 900) {
                $gotoTop.show();
            }
            else {
                $gotoTop.hide();
            }
        };

        $('.right_content').scroll(onScroll);
        onScroll();

        // go-top:
        $gotoTop.click(function () {
            //console.log('click');
            $('.right_content').animate({ scrollTop: 0 }, 1000);
        });

        /*$('.platform-node-name').dblclick(function () {

            var name = $(this).text();
            var command = '"C:\\Program Files (x86)\\NetSarang\\Xmanager Enterprise 5\\Xshell.exe" -url ssh://system:abc123@' + name.trim() + ':22';
            window.oldOnError = window.onerror;
            window._command = command;
            window.onerror = function (err) {
                if (err.indexOf('utomation') != -1) {
                    alert('命令' + window._command + ' 已经被用户禁止！');
                    return true;
                }
                else
                    return false;
            };

            var wsh = new ActiveXObject('WScript.Shell');
            if (wsh)
                wsh.Run(command);
            window.onerror = window.oldOnError;
        });*/

        $('.platform-node-name').dblclick(function () {
            var ssh_link=null;
            if (location.pathname === '/display/' ){
                ssh_link = "SSH://root:abc123@" + $(this).text().split(' ')[0] + ":22";
            }else {
                ssh_link = "SSH://system:abc123@" + $(this).text() + ":22";
            }
            window.open(ssh_link, '_blank');
        });

    });

    function altRows(){
            var tables = $('.altrowstable');
            for (var j = 0; j < tables.length; ++j) {
                var rows = $(tables[j]).find("tr");
                //console.log(rows.length);
                for (var i = 0; i < rows.length; i++) {
                    if (i % 2 == 0) {
                        $(rows[i]).css('background-color', '#ffffff');
                    } else {
                        $(rows[i]).css('background-color', '#efefef');
                    }
                }

                var values = $(tables[j]).find('.itemvalue');
                var rep=/\b(n|unknown)\b/i;
                for (i = 0; i < values.length; i++) {
                    if (rep.test($(values[i]).text() )) {
                        $(values[i]).css('color', '#ff0000');
                    }
                }
            }

            var valids = $('.Wdate');
            for (i = 0; i < valids.length; i++) {
                checkValidity(valids[i]);
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
          //console.log(t);
          var div_date = $(t).parent();
          var pf = $(t).parents('.content_item');
          var site_n = pf.find('label.sitename');
          var pf_n = pf.find('label.platformname');
          var a_pf = $("#a-"+site_n.text()+'-'+pf_n.text());
          var sp = div_date.find('span');
          var i_str = $(t).val().trim();
          var i_Date = Date.parse(i_str);
          var c_Date = Date.parse(new Date());

          //console.log(i_Date);
          //console.log(c_Date);
          if ((i_str === '') || (i_Date + 86400000 <= c_Date)){
            sp.attr('class', 'uk-icon-close');
            a_pf.css('color', '#00ff00');
          }
          else{
            sp.attr('class', 'uk-icon-check');
            a_pf.css('color', 'red');
          }
    }

    function onClickSelectDate(t) {
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
          autoUpdateOnChanged: checkValidity(t)
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
                //console.log('beforeSend');
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
                //console.log('complete');
                $b1.attr('disabled', false);
            },
            error: function () {
                //console.log('error');
                $err.text('Failed');
                $err.css('color', '#ff0000');
            }
        });

    }

    function dbclick_display_tty(t) {
        //console.log('host:');
        var $pppp = $(t).parents('.column_item');
        var host = $pppp.find('.dm_host').text().split(' ')[0];
        var $err = $pppp.find('#error_message');
        var $old = $pppp.find('.tty_text[active="True"]');
        var prefix = 'ChTTY: ';

        if ($(t).attr('active') == 'True') {
            $err.text(prefix+'No change');
            $err.css('color', '#e28327');
            return;
        }

        var $dpy = $(t).parents('.dpy_info');
        var $n_t_i = $dpy.find('>input');
        //console.log(host);
        //console.log(tty);

        var jqxhr = $.ajax({
            url: '/submit_tty/',
            async: true,
            data: {
                    host: host,
                    tty: $(t).text(),
                    n_time: $n_t_i.val()
                },
            dataType: 'json', type: "POST",
        beforeSend: function () {
            //console.log('beforeSend');
            $(t).css('outline', 'outset');
            $err.text(prefix+'Submitting...');
            $err.css('color', '#e28327');
        },
        success: function (res) {
            //console.log('success');
            //console.log(res);
            $err.text(prefix+res['ret']);
            if (res['ret'] != 'Successful'){
                $err.css('color', '#ff0000');
            }else {
                $err.css('color', '#00ff00');
                $old.attr('active', 'False');
                $(t).attr('active', 'True');
                $n_t_i.val(res['n_t']);
            }
        },
        complete: function () {
            //console.log('complete');
            $(t).css('outline-style', 'none');
        },
        error: function (req, errmsg, exception) {
            //console.log('error');
            //console.log('errmsg'+errmsg);
            //console.log('exception'+exception);
            $err.css('color', '#ff0000');
            if (errmsg){
                $err.text(prefix+errmsg);
            }else{
                $err.text(prefix+'Failed');
            }
        }
    });

    }


    function onclick_restart_mmi_btn(t) {
        //console.log('host:');
        var $pppp = $(t).parents('.column_item');
        var host = $pppp.find('.dm_host').text().split(' ')[0];
        var $err = $pppp.find('#error_message');
        var $timeout = $pppp.find('.timeout_value');

        var $node_inf = $(t).parent();
        var $node_txt = $node_inf.find('.node_text');
        var $node_n = $node_txt.text();
        var $n_t_i = $node_inf.find('#last-modified-'+$node_n.trim());
        var prefix = 'Restart: ';
        var counter = null;
        var left_s = parseInt($timeout.val());

        //console.log($node_inf);
        //console.log($n_t_i);

        if ($node_txt.text().trim() === ''){
            $err.text(prefix+'Node should not empty!');
            $err.css('color', '#ff0000');
            return;
        }

        if ($node_txt.text().indexOf(' ') != -1){
            $err.text(prefix+'Only allow to restart 1 node!');
            $err.css('color', '#ff0000');
            return;
        }

        if ($n_t_i.attr('run') === 'N'){
            $err.text(prefix+'The node is not running!');
            $err.css('color', '#ff0000');
            return;
        }
        
        function destroy_counter() {
            if (counter) {
                clearInterval(counter);
                counter = null;
            }
            return;
        }

        function count() {
            if (left_s > 0){
                $err.css('color', '#e28327');
                $err.text(prefix+'Left '+left_s +' seconds');
            }
            else {
                destroy_counter();
            }
            left_s--;
        }

        //console.log(host);
        //console.log(tty);

        var jqxhr = $.ajax({
            url: '/submit_restart_mmi/',
            async: true,
            data: {
                    host: host,
                    node: $node_txt.text(),
                    n_time: $n_t_i.val(),
                    timeout: $timeout.val()
                },
            dataType: 'json', type: "POST",
        beforeSend: function () {
            //console.log('beforeSend');
            $(t).attr('disabled', true);
            counter = setInterval(count, 1000);
        },
        success: function (res) {
            //console.log('success');
            destroy_counter();
            //console.log(res);
            if(res['n_t']){
                $n_t_i.val(res['n_t']);
            }
            $err.text(prefix+res['ret']);
            if (res['ret'] != 'Successful'){
                $err.css('color', '#ff0000');
            }else {
                $err.css('color', '#00ff00');
            }
        },
        complete: function () {
            //console.log('complete');
            destroy_counter();
            $(t).attr('disabled', false);
        },
        error: function (req, errmsg, exception) {
            //console.log('error');
            destroy_counter();
            //console.log('errmsg'+errmsg);
            //console.log('exception'+exception);
            $(t).attr('disabled', false);
            $err.css('color', '#ff0000');
            if (errmsg){
                $err.text(prefix+errmsg);
            }else{
                $err.text(prefix+'Failed');
            }
        }
    });

    }

    function dbclick_display_nodes(t) {

        function has_node_stopped(t1, t2) {
            var n1 = t1.split(' ').filter(function(x){return x!=''});
            var n2 = t2.split(' ').filter(function(x){return x!=''});
            var ch = n1.filter(function (v) {return n2.indexOf(v) == -1})
                .concat(n2.filter(function (v) {return n1.indexOf(v) == -1}));
            //console.log(ch);
            for(var n_i=0; n_i < ch.length; n_i++) {
                var $n_e = $('#last-modified-' + ch[n_i]);
                if ($n_e.attr('run') === 'N') {
                    return true;
                }
            }
            return false;
        }

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
            return JSON.stringify(nodes) ;
        }
        if ($(t).children("input").length > 0) {
            return false;
        }
        //console.log('host:');
        var $pp = $(t).parents('.tty_info');
        var tty = $pp.find('.tty_text').text();
        var $pppp = $(t).parents('.column_item');
        var host = $pppp.find('.dm_host').text().split(' ')[0];
        var $err = $pppp.find('#error_message');
        //console.log(host);
        //console.log(tty);
        var tdDom = $(t);
        //保存初始值
        var tdPreText = $(t).text();
        var width = $(t).width();
        var roll_back = false;
        var node_inf = null;
        var node_txt = null;
        var prefix = 'ChNode: ';

        //var padding = $(t).css('padding-left');
        //给td设置宽度和给input设置宽度并赋值
        $(t).html("<input type='text'>").find("input").width(width).val(tdPreText.trim()).focus();
        //失去焦点的时候重新赋值
        var inputDom = $(t).find("input");
        inputDom.blur(function () {
            var newText = $(this).val();
            if (newText.trim() === tdPreText.trim()){
                $err.text(prefix+'No change');
                $err.css('color', '#e28327');
                roll_back = true;
           /* }else if(newText.trim() === ''){
                $err.text(prefix+'Not allowed to remove!');
                $err.css('color', '#ff0000');
                roll_back = true; */
            }
            else {
                var all_nodes = get_all_nodes(newText);
                var jqxhr = $.ajax({
                    url: '/submit_display/',
                    //url: '/submit1212_display/',
                    async: true,
                    data: {
                        host: host,
                        ns: newText,
                        tty: tty,
                        n_time: all_nodes
                    },
                    dataType: 'json',
                    type: "POST",
                    beforeSend: function () {
                        //console.log('beforeSend');
                        $(t).parent().css('outline', 'outset');
                        if (has_node_stopped(tdPreText, newText)){
                            $err.text(prefix+'Some node stopped. Waiting...');
                        }else{
                            $err.text(prefix+'Submitting...');
                        }
                        $err.css('color', '#e28327');
                    },
                    success: function (res) {
                        //console.log('success');
                        //console.log(res);
                        $err.text(prefix+res['ret']);
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
                                    //console.log($tty_info);
                                    node_txt = $tty_info.find('.node_text');
                                    node_inf = $tty_info.find('.node_info');
                                    //console.log(node_txt);
                                    node_inf.attr('conflict', cx['c']);
                                    node_inf.find('input.last-modified-time').remove();
                                    $(t).find('input').remove();
                                    if (cx['ns'] === ''){
                                        node_txt.html('&nbsp;');
                                        node_txt.attr('title', '');
                                    }else{
                                        node_txt.text(cx['ns']);
                                        node_txt.attr('title', cx['ns']);
                                        for(var t_i=0;t_i<cx['n_time'].length;t_i++){
                                            node_txt.after('<input type="hidden" class="last-modified-time" id="last-modified-'
                                            +cx['n_time'][t_i]['n']
                                            +'" value="'
                                            +cx['n_time'][t_i]['t'] 
                                            +'" run="'
                                            +cx['n_time'][t_i]['r']
                                            +'" />');
                                        }
                                    }
                                }
                            }
                        }
                    },
                    complete: function () {
                        //console.log('complete');
                        $(t).parent().css('outline-style', 'none');
                    },
                    error: function (req, errmsg, exception) {
                        //console.log('error');
                        //console.log('errmsg'+errmsg);
                        //console.log('exception'+exception);
                        $err.css('color', '#ff0000');
                        if (errmsg){
                            $err.text(prefix+errmsg);
                        }else{
                            $err.text(prefix+'Failed');
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

    function onblurTimout(t) {
        var $err = $(t).parents(".column_item").find('#error_message');
        var $old = $(t).next();
        var newText = $(t).val();
        var oldText = $old.val();
        $err.text("");
        if ((newText.trim() === '')||(!parseInt(newText))||(newText < 180) ){
            $err.text("Timeout should > 180");
            $err.css('color', '#ff0000');
            $(t).val(oldText);
        }
        else{
            $old.val(newText);
        }
    }

    function altBackendRow() {
        //console.log(altBackendRow);
        var $tbody = $('tbody');
        var $td = $tbody.find('td').filter(function(x) {
                                        return $(this).text() === 'Collecting';
                                    });
        if($td){
            var $tr = $td.parent();
            $tr.css('background-color', '#ff0000');
        }


        function display_cur_time() {
            var c_Date = new Date();
            $('#current-time').text(c_Date.toISOString().replace('T', ' ').replace('Z', ''));

        }

        counter = setInterval(display_cur_time, 1000);
        $('#pf-num').text($('tr').length-1);
    }

    function closeConn() {
        if(window.s) {
            window.s.close();
            $("#real_time_state").text('closed');
            window.s = null;
        }
    }

    function onclickwebsocketbtn(){
        //console.log("onclickwebsocketbtn");
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
            //console.log(event);
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
                    //console.log('insert at first!');
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
                    //console.log('insert after current tr!');
                    c_tr.after(to_insert);
                }
            }
            to_del.forEach(function (x) {
                x.remove();
            });
            //c_tr.css('background-color', '#ff0000');
            state.text('updated');
            altBackendRow();
            //$('#pf-num').text($('tr').length-1);
        };
        socket.onclose = function (event) {
            /* 服务器端主动断开连接时，自动执行 */
            state.text('Closed or limit reached!');
            btn.text("Start Real Time Monitor");
            window.s = null;
        };


    }