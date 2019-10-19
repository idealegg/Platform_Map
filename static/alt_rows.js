/**
 * Created by huangd on 2019/9/10.
 */
    function altRows(id){
      if(document.getElementsByTagName){

        var table = document.getElementById(id);
        var rows = table.getElementsByTagName("tr");
        console.log(rows.length);
        for(i = 0; i < rows.length; i++){
          if(i % 2 == 0){
            rows[i].style.backgroundColor='#ffffff';
          }else{
            rows[i].style.backgroundColor='#efefef';
          }
        }

        var values = table.getElementsByClassName('itemvalue');
        for(i = 0; i < values.length; i++){
          if((values[i].innerHTML == 'N') || (values[i].innerHTML == 'n') || (values[i].innerHTML == 'unknown')
                          || (values[i].innerHTML == 'Unknown')|| (values[i].innerHTML == 'UNKNOWN')){
            values[i].style.color = '#ff0000';
          }
        }

        var validitys = document.getElementsByClassName('validity');
        for (i = 0; i < validitys.length; i++){
          checkValidity(validitys[i]);
        }
      }
    }

    function altRow(t){
      console.log('altRow');
      console.log(t.id);
      if(t.id % 2 == 0){
        t.style.backgroundColor='#ffffff';
      }else{
        t.style.backgroundColor='#efefef';
      }
    }

    function onClickItem(t, item) {
      console.log('onClickItem');
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

    function onClickPlatform(t, t2) {
      console.log('onClickPlatform');
      console.log(t);
      console.log(t2);
      var form = document.createElement('form');
      form.action = '#';
      form.method = 'post';
      var input = document.createElement('input');
      input.type = 'hidden';
      input.name = 'site';
      input.value = t2;
      form.appendChild(input);
      var input2 = document.createElement('input');
      input2.type = 'hidden';
      input2.name = 'platform';
      input2.value = t.innerHTML;
      form.appendChild(input2);
      document.body.append(form);
      form.submit();
    }

    function checkValidity(t) {
          console.log('checkValidity')
          console.log(t);
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
        console.log(t);
        console.log(t2);
      WdatePicker({
          el: t, //点击对象id，一般可省略el
          lang: 'en', //语言选择，一般用auto
          dateFmt: 'MMM. d, yyyy', //时间显示格式，年月日 时分秒，年月日就是yyyy-MM-dd
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

    function submit_platform(site, pf) {
      console.log('submit_platform');
      var form = document.createElement('form');
      form.action = '#';
      form.method = 'post';
      var all_clear = true;  
      var input;
      mapping =[
           ['description', 'description'],
           ['owner', 'owner'],
           ['validity', 'Wdate']
            ];
       for(var i=0;i<mapping.length; i++) {
          input = document.createElement('input');
          input.type = 'hidden';
          input.name = mapping[i][0];
          input.value = document.getElementsByClassName(mapping[i][1])[0].value;
          if (input.value != ''){
              all_clear = false;
          }
          if (input.name == 'validity'){
              if (input.value != "") {
                  console.log(input.value);
                  var date = new Date(Date.parse(input.value));
                  console.log(date);
                  input.value = date.getFullYear() + '-' + (date.getMonth() + 1) + '-' + date.getDate();
              }
          }
          console.log(input.name);
          console.log(input.value);

          form.appendChild(input);
      }

      input = document.createElement('input');
      input.type = 'hidden';
      input.name = 'info';
      if (all_clear) {
          input.value = site + ' ' + pf +' Y';
      }else {
          input.value = site + ' ' + pf +' N';
      }
      console.log(input.value) ;
      form.appendChild(input);
      document.body.append(form);
      form.submit();
    }
