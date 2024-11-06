console.log('script.js loaded');

jQuery(document).ready(function($) {
    const $btn_example = $('#btn-example');
    const $input_example = $('#input-example');
    const $responseOutput = $('#response-output');

    $btn_example.click(function() {
        const userInput = $input_example.val();
        console.log(`Input: ${userInput}`);

        $.ajax({
            url: `${ROOT_PATH}/api/${userInput}`,
            type: 'GET',
            success: function(response) {
                console.log(response);

                const prettyResponse = JSON.stringify(response, null, 2);  // Indent with 2 spaces
                $responseOutput.text(prettyResponse);  // Insert the formatted JSON into the <pre> tag
            },
            error: function(xhr, status, error) {
                console.error(xhr, status, error);

                const errorMessage = `Error fetching data: ${error}`;
                $responseOutput.text(errorMessage);
            }
        });
    });
});
