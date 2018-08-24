$(document).ready(function() {
    $('.btn-success').click(function (){
        var btn = $(this).data();
        $('#unirec_file').val(btn.path);
    })
});