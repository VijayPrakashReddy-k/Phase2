'use strict';

(function($) {

  $(document).ready(function () {
    // Check for FileReader API (HTML5) support.
    if (!window.FileReader) {
      alert('This browser does not support the FileReader API.');
    }
  });

  $.retryAjax = function (ajaxParams) {
    var errorCallback;
    ajaxParams.tryCount = (!ajaxParams.tryCount) ? 0 : ajaxParams.tryCount;
    ajaxParams.retryLimit = (!ajaxParams.retryLimit) ? 2 : ajaxParams.retryLimit;
    ajaxParams.suppressErrors = true;

    if (ajaxParams.error) {
        errorCallback = ajaxParams.error;
        delete ajaxParams.error;
    } else {
        errorCallback = function () {

        };
    }

    ajaxParams.complete = function (jqXHR, textStatus) {
        if ($.inArray(textStatus, ['timeout', 'abort', 'error']) > -1) {
            this.tryCount++;
            if (this.tryCount <= this.retryLimit) {

                // fire error handling on the last try
                if (this.tryCount === this.retryLimit) {
                    this.error = errorCallback;
                    delete this.suppressErrors;
                }

                //try again
                console.log("Trying again");
                $.ajax(this);
                return true;
            }

            window.alert('There was a server error.  Please refresh the page.  If the issue persists, give us a call. Thanks!');
            return true;
        }
    };

    $.ajax(ajaxParams);
  };

  var url = {
    "week1": "https://jzworltk54.execute-api.ap-south-1.amazonaws.com/dev/classify",
    "week2": "https://jzworltk54.execute-api.ap-south-1.amazonaws.com/dev/classify",
    "face_swap": "https://zuav5qg7sc.execute-api.ap-south-1.amazonaws.com/dev/face_swap"
  };

  // Utils

  function getFileReader(imgId) {
    let reader = new FileReader();
    reader.onload = function(e) {
      $("#"+imgId).attr('src', e.target.result);
    };
    return reader;
  };
  var reader = getFileReader("upImage")

  function showImage(input) {
    if (input.files && input.files[0]) {
      $("#imgClass").text("");
      reader.readAsDataURL(input.files[0]);
    }
  }

  $("input#getFile").change(function(){
    showImage(this);
  });

  $("#classifyImage1").click(function(){
    return classify("week1")
  });

  $("#classifyImage2").click(function(){
    return classify("week2")
  });

  $("#faceSwap").click(function(){
    var documentData = new FormData();
    $.each($('input#getFile')[0].files,function(i, file){
      documentData.append("files["+i+"]", file)
    });
    $.ajax({
      url: url["face_swap"],
      type: 'POST',
      data: documentData,
      async: false,
      cache: false,
      contentType: false,
      processData: false,
      timeout:5000,
      success: function (response) {
          $("#file1").attr('src', 'data:image/png;base64,'+ response["file1"][1])
          $("#file2").attr('src', 'data:image/png;base64,'+ response["file2"][1])
      },
      error: function(e) {
        alert(e.responseText)
      }
  });
  })

  function classify(url_key) {
    var documentData = new FormData();

    // Post the file to url and get response
    documentData.append("body", $('input#getFile')[0].files[0]);
    $.retryAjax({
        url: url[url_key],
        type: 'POST',
        data: documentData,
        async: false,
        cache: false,
        contentType: false,
        processData: false,
        timeout:5000,
        success: function (response) {
            $("#imgClass").text(response.predicted)
        },
        error: function(e) {
          alert(e.responseText)
        }
    });
    return false;
  }

  // Display error messages.
  function onError(error) {
    alert(error.responseText);
  }

})(jQuery)
