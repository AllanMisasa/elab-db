        $(document).ready(function() {
            $('#product_name').on('input', function() {
                var search_term = $(this).val();
                if (search_term.length > 1) {
                    $.ajax({
                        url: '/presearch',
                        data: {
                            term: search_term
                        },
                        success: function(data) {
                            $('#presearch-results').empty();
                            if (data.length > 0) {
                                $.each(data, function(index, item) {
                                    $('#presearch-results').append('<a href="#" class="list-group-item list-group-item-action">' + item + '</a>');
                                });
                                $('#presearch-results').width($('#product_name').width());
                            } else {
                                $('#presearch-results').append('<a href="#" class="list-group-item list-group-item-action disabled">Intet match fundet i databasen.</a>');
                                $('#presearch-results').width($('#product_name').width());
                            }
                            $('#presearch-results').show();
                        }
                    });
                } else {
                    $('#presearch-results').empty();
                    $('#presearch-results').hide();
                }
            });

            $('#presearch-results').on('click', '.list-group-item', function(event) {
                event.preventDefault();
                var value = $(this).text();
                $('#product_name').val(value);
                $('#presearch-results').empty();
                $('#presearch-results').hide();
                $('#search-form').submit();
            });

            $(document).click(function(event) {
                if (!$(event.target).closest('#presearch-results').length) {
                    $('#presearch-results').empty();
                    $('#presearch-results').hide();
                }
            });
        });