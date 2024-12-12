$(document).ready(function() {

    // Set the CSRF token so that we are not rejected by server
    var csrf_token = $('meta[name=csrf-token]').attr('content');
    // Configure ajaxSetupso that the CSRF token is added to the header of every request
  $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrf_token);
            }
        }
    });

    // Attach a function to trigger when users click like
    $(document).ready(function() {
        $("#like-button").on("click", function() {
            // Make an AJAX POST request
            $.ajax({
                url: "/like",
                type: "POST",
                data: JSON.stringify({response: $(this).attr('id')}),
                success: function(response) {
                    // Update the like count in the DOM
                    $("#like-count").text(response.likes);
                },
                error: function() {
                    alert("Error liking the post. Please try again.");
                }
            });
        });
    });
});