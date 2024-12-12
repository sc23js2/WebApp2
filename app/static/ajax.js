function likeProduct(productId) {
    fetch('/like', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ product_id: productId })
    })

    .then(response => response.json())
    .then(data => {
        if (data.success) {
               
            //increase like count
            const likesElement = document.getElementById(`likes-${productId}`);
            likesElement.textContent =  "This product has " + data.likes + " likes 🖤";

        } else {
            console.error("Error: product not liked");
        }
    })

}
