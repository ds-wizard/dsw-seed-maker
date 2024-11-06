jQuery(document).ready(function($) {
            const $btn_example = $('#btn-example');
            const $input_example = $('#input-example');
            const $responseOutput = $('#response-output');
            const $copyBtn = $('#copy-btn');

            function fetchData() {
                const userInput = $input_example.val();
                $.ajax({
                    url: `${ROOT_PATH}/api/${userInput}`,
                    type: 'GET',
                    success: function(response) {
                        const prettyResponse = JSON.stringify(response, null, 2);
                        $responseOutput.val(prettyResponse);
                        $responseOutput.prop('readonly', false);
                    },
                    error: function(xhr, status, error) {
                        const errorMessage = `Error fetching data: ${error}`;
                        $responseOutput.val(errorMessage);
                        $responseOutput.prop('readonly', true);
                    }
                });
            }

            $btn_example.click(fetchData);

            $input_example.keypress(function(event) {
                if (event.key === "Enter") {
                    event.preventDefault();
                    fetchData();
                }
            });

            $copyBtn.click(function() {
                const content = $responseOutput.val().trim();
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
