$(document).ready(function() {
    $('#unirec_file').modal('hide');
    $('.btn-success').click(function (){
        var btn = $(this).data();
        $('#unirec_file').val(btn.path);
        $('#myModal').modal('toggle');
    })
});