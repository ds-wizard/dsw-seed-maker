jQuery(document).ready(function ($) {
    const $btn_copy = $('#btn-copy');
    const $btn_list = $('#btn-list');
    const $input_search = $('#input-search');
    const $output_search = $('#output-search');

    function fetchData() {
        const userInput = $input_search.val();
        $.ajax({
            url: `${ROOT_PATH}/api/${userInput}`,
            type: 'GET',
            success: function (response) {
                const prettyResponse = JSON.stringify(response, null, 2);
                $output_search.val(prettyResponse);
                $output_search.prop('readonly', false);
            },
            error: function (xhr, status, error) {
                const errorMessage = `Error fetching data: ${error}`;
                $output_search.val(errorMessage);
                $output_search.prop('readonly', true);
            }
        });
    }

    $btn_list.click(fetchData);

    $input_search.keypress(function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            fetchData();
        }
    });

    $btn_copy.click(function () {
        const content = $output_search.val().trim();
        try {
            JSON.parse(content);
            navigator.clipboard.writeText(content)
                .then(() => alert("Valid JSON copied to clipboard!"))
                .catch(err => console.error("Failed to copy: ", err));
        } catch (error) {
            alert("The content in the text area is not valid JSON. Please correct it before copying.");
        }
    });
});
