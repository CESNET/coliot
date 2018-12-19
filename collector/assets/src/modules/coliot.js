$(document).ready(function() {
    if ($("#unirec_file").length){
    $('#unirec_file').hide();

    var files = $('#unirec_file').val();
    var file_list = files.split(';');
    var modal = '';
    for(var i=0; i<file_list.length-1;i++){
        modal = modal + '<tr> <td>'+file_list[i]+'</td> <td>root</td> <td>28.08.2018 11:21</td> <td>.md</td> <td>342 Kb</td> <td><p data-placement="top" data-toggle="tooltip" title="Edit"><div class="btn btn-success btn-xs" data-title="Edit" data-toggle="modal" data-target="#edit" data-path="'+file_list[i]+'"><span class="glyphicon glyphicon-open"></span></div></p></td> </tr>'
    }
    $("#file_name").append(modal);

    $('.btn-success').click(function (){
        var btn = $(this).data();
        $('#unirec_file').val(btn.path);
        $('#myModal').modal('toggle');
    })
    }

});
