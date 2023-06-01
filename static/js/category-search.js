$(document).ready(function() {
    $('#search-by-category-button').click(function() {
        // show the category search form
        $('#category-search-form').show();
    });

    // populate the category dropdown
    $.ajax({
        url: '/categories',
        success: function(categories) {
            var categoryDropdown = $('#category-dropdown');
            $.each(categories, function(index, category) {
                categoryDropdown.append($('<option></option>').text(category).val(category));
            });
        }
    });

    // submit the category search form
    $('#category-search-form').submit(function(event) {
        event.preventDefault();
        var category = $('#category-dropdown').val();
        $.ajax({
            url: '/category-search',
            data: { category: category },
            success: function(results) {
                var table = $('#category-search-results');
                table.empty();
                table.append('<thead><tr><th>Ark nr.</th><th>Shelf nr.</th><th>Vertical</th><th>Horizontal</th><th>Product name</th><th>Part Category</th><th>Total on shelf</th><th>Bemærkninger:</th><th>Link:</th></tr></thead><tbody>');
                $.each(results, function(index, row) {
                    var tr = $('<tr></tr>');
                    $.each(row, function(index, cell) {
                        tr.append($('<td></td>').text(cell));
                    });
                    table.append(tr);
                });
                table.append('</tbody>');
                $('#category-search-results-section').show();
            }
        });
    });
});