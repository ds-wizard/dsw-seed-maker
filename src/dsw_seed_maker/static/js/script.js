jQuery(document).ready(function ($) {
    const $btn_copy = $('#btn-copy');
    const $btn_list = $('#btn-list');
    const $btn_process = $('#btn-process');  // Add reference to the "Process" button
    const $input_search = $('#input-search');
    const $output_search = $('#output-search');

    // Function to fetch data from the API
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

    // Function to call the process API endpoint
    function processData() {
        const inputData = $output_search.val();  // Get the current content of the output_search (editable textbox)

        $.ajax({
            url: `${ROOT_PATH}/api/process`,  // Call the new endpoint
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ data: inputData }),  // Send the input data
            success: function (response) {
                const processedData = JSON.stringify(response, null, 2);
                $output_search.val(processedData);  // Display the processed data in the textbox
                $output_search.prop('readonly', false);
            },
            error: function (xhr, status, error) {
                const errorMessage = `Error processing data: ${error}`;
                $output_search.val(errorMessage);
                $output_search.prop('readonly', true);
            }
        });
    }

    // Button click event handlers
    $btn_list.click(fetchData);
    $btn_process.click(processData);  // Attach processData to the "Process" button click

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
