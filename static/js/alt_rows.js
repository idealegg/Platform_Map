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
          var c_Date = new Date();
          if (i_Date >= c_Date){
            sp.className = 'status correct';
          }
          else{
            sp.className = 'status incorrect';
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
        var jqxhr = $.ajax({
            url: '/submit_platform/',
            async: true,
            data:
            {
            site: site,
            pf: pf,
            desc: $inputs.get(0).value,
            owner: $inputs.get(1).value,
            valid: $valid},
            type: "POST",
            beforeSend: function () {
                console.log('beforeSend');
                $b1.attr('disabled', true);
            },
            success: function (res) {
                //console.log('success');
                //console.log(res);
                $err.text(res);
               // $b1.attr('disabled', false);
            },
            complete: function () {
                console.log('complete');
                $b1.attr('disabled', false);
            },
            error: function () {
                //console.log('error');
                $err.text('Failed');

            }
        });

    }

    function dbclick_tty_nodes(t) {
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
        var response = 'Failed';
        //var padding = $(t).css('padding-left');
        //给td设置宽度和给input设置宽度并赋值
        $(t).html("<input type='text'>").find("input").width(width).val(tdPreText).focus();
        //失去焦点的时候重新赋值
        var inputDom = $(t).find("input");
        inputDom.blur(function () {
            var newText = $(this).val();
            if(newText.trim() === ''){
                $err.text('Not allowed to remove!');
            }
            else if (newText.trim() === tdPreText.trim()){
                $err.text('No change');
            }else{

                var jqxhr = $.ajax({
                    url: '/submit_display/',
                    //url: '/submit1212_display/',
                    async: true,
                    data: {
                        host: host,
                        ns: newText,
                        tty: tty
                    },
                    dataType: 'json',
                    type: "POST",
                    beforeSend: function () {
                        console.log('beforeSend');
                        $(t).parent().css('outline', 'outset');
                    },
                    success: function (res) {
                        console.log('success');
                        //console.log(res);
                        $err.text(res['ret']);
                       // $b1.attr('disabled', false);
                        if (res['ret'] != 'Successful'){
                            tdDom.text(tdPreText);
                        }
                        if (res['cx'].length > 0 ){
                            for(var i = 0;i < res['cx'].length;++i ){
                                var cx = res['cx'][i];
                                var $h = $(document).find('#div-'+cx['host']);
                                var $tty_info = $h.find('.tty_text').filter(
                                    function(x) {
                                        return $(this).text() === 'TTY'+cx['tty'];
                                    }).parent();
                                $tty_info.attr('conflict', cx['c']);
                                $tty_info.find('.node_text').text(cx['ns']);
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
                        if (errmsg){
                            $err.text(errmsg);
                        }else{
                            $err.text('Failed');
                        }
                        tdDom.text(tdPreText);
                    }
                });
            }
            $(this).remove();
            tdDom.text(newText);
        });
    }

