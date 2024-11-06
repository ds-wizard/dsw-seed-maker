console.log('script.js loaded');

jQuery(document).ready(function($) {
    const $btn_example = $('#btn-example');
    const $input_example = $('#input-example');

    $btn_example.click(function() {
        const userInput = $input_example.val();
        console.log(`Input: ${userInput}`);

        if (userInput === 'users') {
            // Send GET request to fetch users
            $.ajax({
                url: `${ROOT_PATH}/api/users`,
                type: 'GET', // Change to GET
                success: function(response) {
                    console.log(response);
                    alert(`Got users from server: ${JSON.stringify(response)}`);
                    // Render users on the webpage or do something else with the response
                },
                error: function(xhr, status, error) {
                    console.error(xhr, status, error);
                    alert(`Error fetching users: ${error}`);
                }
            });
        } else {
            // Original functionality for example
            alert('Button clicked, sending AJAX request');
            $btn_example.prop('disabled', true); // no clicking when processing

            const magicCode = $input_example.val();
            console.log(`Sending magic code: ${magicCode}`);

            $.ajax({
                url: `${ROOT_PATH}/api/example`,
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    magicCode: magicCode,
                    message: 'Hello, server!',
                }),
                success: function(response) {
                    console.log(response);
                    alert(`Got response from server: ${response.message}`);
                    $btn_example.prop('disabled', false); // re-enable the button
                },
                error: function(xhr, status, error) {
                    console.error(xhr, status, error);
                    alert(`Error: ${error}`);
                    $btn_example.prop('disabled', false); // re-enable the button
                }
            });
        }
    });
});
