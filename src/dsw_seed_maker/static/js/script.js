console.log('script.js loaded')

jQuery(document).ready(function($) {
    const $btn_example = $('#btn-example')
    const $input_example = $('#input-example')

    $btn_example.click(function() {
        alert('Button clicked, sending AJAX request')
        $btn_example.prop('disabled', true) // no clicking when processing

        const magicCode = $input_example.val()
        console.log(`Sending magic code: ${magicCode}`)

        $.ajax({
            url: `${ROOT_PATH}/api/example`,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                magicCode: magicCode,
                message: 'Hello, server!',
            }),
            success: function(response) {
                console.log(response)
                alert(`Got response from server: ${response.message}`)
                // Here you can render something in the webpage (e.g. form elements)

                $btn_example.prop('disabled', false)  // re-enable the button
            },
            error: function(xhr, status, error) {
                console.error(xhr, status, error)
                alert(`Error: ${error}`)
                // Here you can render an error message in the webpage

                $btn_example.prop('disabled', false)  // re-enable the button
            }
        })
    })
})

// classes and other functions to do something with the webpage and data
