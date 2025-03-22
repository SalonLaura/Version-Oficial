function addProduct(id,nombre,medida,codigo,existencia){
    
    const elemento = document.getElementById(`producto-transferir-${id}`);
    if (elemento) { return }

    document.getElementById("input-search").focus()
    document.getElementById("input-search").select()
    let content = document.getElementById("content-products");

    const newProduct = document.createElement('div');
    newProduct.id = `product-content-${id}`;
    newProduct.innerHTML = `
    <input type="number" step="0.01" step-my  name="product-id" value=${id} class="hidden" id="producto-transferir-${id}">
    <div class="flex w-1/2">
        <div class="flex w-1/6 border">
            <button type="button" class="text-red-500 px-1 material-icons text-md" onclick="removedProduct(${id})">delete_outline</button>
            <span class="w-full text-start flex items-center">${codigo}</span>
        </div>
        <span class="w-2/6 border text-center">${nombre}</span>
        <span class="w-1/6 border text-center">${medida}</span>
         <div class="flex w-2/6 border">
            <input type="date" class=" bg-yellow-100 margin:0; padding:0; border:0;" id="product-vencimiento-${id}" name="product-vencimiento"  />            
        </div>
    </div>
    <div class="flex w-1/2 border">
        <div class="flex w-1/2 h-full border-r">
            <div class="flex w-1/3 border-r">
                <span class="text-red-500">*</span>
                <input type="number" step="0.01" step-my  id="product-cantidad-${id}" name="product-cantidad" class="item-form bg-transparent border-0 text-md  block w-full p-0.5 focus:ring-0 appearance-none focus:outline-none focus:ring-0 " min="0" step="0.01" placeholder="" required  oninput="calcularImporte('${id}')">
            </div>
            <div class="flex w-2/3 border-l">
                <span class="text-red-500">*</span>
                <div class="flex w-full">
                    <input type="number" step="0.01" step-my  id="product-precio-1-${id}" name="product-precio-1" class="item-form bg-transparent border-0 text-md  block w-3/5 p-0.5 focus:ring-0 appearance-none focus:outline-none focus:ring-0 " min="0" step="0.01" placeholder="" required oninput="calcularImporte('${id}')">
                    <span class="w-0.5 bg-gray-200"></span>
                    <input type="number" step="0.01" step-my  id="product-precio-2-${id}" name="product-precio-2" class="item-form bg-transparent border-0 text-md  block w-2/5 p-0.5 focus:ring-0 appearance-none focus:outline-none focus:ring-0" min="0" step="0.01" placeholder="" required oninput="calcularImporte('${id}')">
                </div>
            </div>
        </div>
        <div class="flex w-1/2">
            <div class="flex w-2/3 border-l">
                <span class="text-center h-full w-3/5 importe-1" id="product-importe-1-${id}">-</span>
                <span class="w-0.5 bg-gray-200"></span>
                <span class="text-center h-full w-2/5 importe-2" id="product-importe-2-${id}">-</span>
            </div>
            <span class="bg-transparent border-0 text-md text-center border-l-2 border-gray-200 block w-1/3 p-0.5 focus:ring-0 appearance-none focus:outline-none focus:ring-0" id="product-existencia-${id}">${existencia}</span>
        </div>
    </div>`;
    newProduct.className = "flex";

    content.appendChild(newProduct);
    document.getElementById("product-"+id).classList.add("hidden");
    document.getElementById("product-"+id).classList.add("product-select");
    //document.getElementById("close-modal-products").click();
    // Quitado de el input de la cantidad onchange="calcularImporte('${id}')"
    // <input type="text" name="existencia" class="item-form bg-transparent border-0 text-md text-center border-l-2 border-gray-200 block w-1/3 p-0.5 focus:ring-0 appearance-none focus:outline-none focus:ring-0" readonly id="product-existencia-${id}" existencia="${existencia}" value="${existencia}">
}

function addGasto(){
    const date = new Date();
    const miliseconds = date.getMilliseconds();

    let content = document.getElementById("content-gastos");

    const newGasto = document.createElement('div');
    newGasto.id = `gasto-${miliseconds}`;
    newGasto.innerHTML = `
    <div class="bg-transparent w-2/3 border border-gray-200 flex">
        <button type="button" class="text-red-500 px-1 material-icons text-md" onclick="document.getElementById('gasto-${miliseconds}').remove()">delete_outline</button>
        <input name="gasto-nombre" class="flex-1 bg-transparent text-md border-0 block p-0.5 focus:ring-0 focus:border-0 appearance-none focus:outline-none focus:ring-0" required/>
    </div>
    <input type="number" step="0.01" step-my  name="gasto-cantidad" class="px-3 border border-gray-200 bg-transparent text-md block w-1/3 p-0.5 focus:ring-0 focus:border-gray-200 appearance-none focus:outline-none focus:ring-0" min="0" step="0.01" placeholder="" required>
    `;
    newGasto.className = "flex";

    content.appendChild(newGasto);

}

function removedProduct(id){
    document.getElementById(`product-content-${id}`).remove();
    document.getElementById("product-"+id).classList.remove("hidden");
    document.getElementById("product-"+id).classList.remove("product-select");
    calcularImporteTotal()
}

function search(){
    var elements = document.getElementsByClassName("item-product");
    for (var i = 0; i < elements.length; i++) {
        if (!elements[i].classList.contains("product-select")) {
            var inputText = document.getElementById("input-search").value.toLowerCase();
            var nameText = document.getElementById(`name-${elements[i].id}`).textContent.toLowerCase();
            var codeText = document.getElementById(`code-${elements[i].id}`).textContent;

            if (nameText.includes(inputText) || codeText.includes(inputText)) {
                elements[i].classList.remove("hidden");
            } else {
                elements[i].classList.add("hidden");
            }
        }
    }
}

function calcularImporte(id){
    let cant = document.getElementById(`product-cantidad-${id}`).value;
    cant.value = parseInt(cant.value);

    /* Lo quite xq sustitui el input del saldo por el input de la existencia
    let element_existencia = document.getElementById(`product-existencia-${id}`);
    if(element_existencia.value != ""){
        element_existencia.value = parseFloat(element_existencia.getAttribute("existencia")) + parseFloat(cant);
    }else{
        element_existencia.value = parseFloat(element_existencia.getAttribute("existencia"));
    }*/


    if(document.getElementById(`product-precio-2-${id}`).value == "" && document.getElementById(`product-precio-1-${id}`).value != ""){
        document.getElementById(`product-precio-2-${id}`).value = "00";
    }
    if(document.getElementById(`product-precio-1-${id}`).value == "" && document.getElementById(`product-precio-2-${id}`).value != ""){
        document.getElementById(`product-precio-1-${id}`).value = "0";
    }

    if(document.getElementById(`product-precio-1-${id}`).value == "" || document.getElementById(`product-precio-2-${id}`).value == "" || cant == ""){
        document.getElementById(`product-importe-1-${id}`).innerText = "-";
        document.getElementById(`product-importe-2-${id}`).innerText = "-";
        return
    }

    let product_precio_1 = document.getElementById(`product-precio-1-${id}`);
    product_precio_1.value = parseInt(product_precio_1.value);
    let product_precio_2 = document.getElementById(`product-precio-2-${id}`);
    //product_precio_2.value = parseInt(product_precio_2.value);
    
    let precio = parseFloat( product_precio_1.value + "." + product_precio_2.value);
        
    let importe = (cant * precio).toString().split(".")

    if( importe[0] == NaN ){
        document.getElementById(`product-importe-1-${id}`).innerText = "-";
        document.getElementById(`product-importe-2-${id}`).innerText = "-";
    }
    else{
        document.getElementById(`product-importe-1-${id}`).innerText = importe[0];
        if(importe[1]){
            if(importe[1].length == 1){
                document.getElementById(`product-importe-2-${id}`).innerText = importe[1] + "0";
            }
            //else if(importe[1].length > 2){
            //    document.getElementById(`product-importe-2-${id}`).innerText = importe[1][0] + importe[1][1];
            //}
            else{
                document.getElementById(`product-importe-2-${id}`).innerText = importe[1];
            }
        }
        else{
            document.getElementById(`product-importe-2-${id}`).innerText = "00";
        }
    }
    
    calcularImporteTotal()
}

function calcularImporteTotal(){
    var importe1Elements = document.getElementsByClassName("importe-1");
    var importe2Elements = document.getElementsByClassName("importe-2");
    var importeTotal = 0.0;
    for (var i = 0; i < importe1Elements.length; i++) {
        var importe1 = importe1Elements[i].textContent;
        var importe2 = importe2Elements[i].textContent;
        if(importe1 !== "-" && importe2 !== "-"){
            importeTotal += parseFloat(importe1 + "." + importe2);
        }
    }
    
    let importe = importeTotal.toString().split(".")

    if( importe[0] == NaN ){
        document.getElementById("product-importe-1").innerText = "-";
        document.getElementById("product-importe-2").innerText = "-";
    }
    else{
        document.getElementById("product-importe-1").innerText = importe[0];
        if(importe[1]){
            if(importe[1].length == 1){
                document.getElementById("product-importe-2").innerText = importe[1] + "0";
            }
            //else if(importe[1].length > 2){
            //    document.getElementById("product-importe-2").innerText = importe[1][0] + importe[1][1];
            //}
            else{
                document.getElementById("product-importe-2").innerText = importe[1];
            }
        }
        else{
            document.getElementById("product-importe-2").innerText = "00";
        }
    }
}


function abrirAgregarProducto(){
    document.getElementById("error-add").classList.add("hidden");
    var t = `
    <h1 class="mb-4 text-xl font-semibold text-gray-700 dark:text-gray-200" >Agregar producto</h1>

    
    <ul class="grid w-full gap-2 md:grid-cols-2">
        <li>
            <input type="radio" id="add-as-producto" onchange="changeProductoToSubproducto(false)" checked name="hosting" value="add-as-producto" class="hidden peer" required>
            <label for="add-as-producto" id="lbl-as-producto" class="text-center text-lg font-semibold inline-flex items-center justify-center w-full py-2 text-gray-500 bg-white border border-gray-200 rounded-full cursor-pointer dark:hover:text-gray-300 dark:border-gray-700 dark:peer-checked:text-blue-500 peer-checked:border-blue-600 peer-checked:text-blue-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">                           
                Agregar como producto
            </label>
        </li>
        <li>
            <input type="radio" id="add-as-subproducto" onchange="changeProductoToSubproducto(true)" name="hosting" value="add-as-subproducto" class="hidden peer">
            <label for="add-as-subproducto" id="lbl-as-subproducto" class="text-center text-lg font-semibold inline-flex items-center justify-center w-full py-2 text-gray-500 bg-white border border-gray-200 rounded-full cursor-pointer dark:hover:text-gray-300 dark:border-gray-700 dark:peer-checked:text-blue-500 peer-checked:border-blue-600 peer-checked:text-blue-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">                           
                Agregar como subproducto
            </label>
        </li>
    </ul>

    <div class="space-y-4">
    <div class="">
        <p class="text-gray-700 dark:text-gray-400 m-1.5">Nombre</p>
        <input class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-purple-500 focus:border-purple-500 block w-full p-2.5 dark:bg-gray-600 dark:border-gray-500 dark:placeholder-gray-400 dark:text-white"
            placeholder="" type="text" maxlength="100" id="nombre" required/>
    </div>
    <div class="">
        <p class="text-gray-700 dark:text-gray-400 m-1.5">Descripción</p>
        <input class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-purple-500 focus:border-purple-500 block w-full p-2.5 dark:bg-gray-600 dark:border-gray-500 dark:placeholder-gray-400 dark:text-white"
            placeholder="" type="text" maxlength="300" id="descripcion" required/>
    </div>
    <div class="flex space-x-2">
        <div class="w-1/2">
            <p class="text-gray-700 dark:text-gray-400 m-1.5">Código</p>
            <input class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-purple-500 focus:border-purple-500 block w-full p-2.5 dark:bg-gray-600 dark:border-gray-500 dark:placeholder-gray-400 dark:text-white"
                placeholder="" type="text" maxlength="100" id="codigo" required/>
        </div>

        <div class="w-2/3">
            <p class="text-gray-700 dark:text-gray-400 m-1.5">Unidad de medida</p>
            <select class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-purple-500 focus:border-purple-500 block w-full p-2.5 dark:bg-gray-600 dark:border-gray-500 dark:placeholder-gray-400 dark:text-white"
            id="medida" required>`
        
	window.objMedidas.forEach(medida => {
        t += `<option value="${medida.id}">${medida.nombre}</option>`
	})
    
    t += `<select/>
    </div>    
    </div>


    <div class="flex space-x-2" id="content-options-subproducto">
        <div class="w-1/2">
            <p class="text-gray-700 dark:text-gray-400 m-1.5">Precio de venta (CUP)</p>
            <input class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-purple-500 focus:border-purple-500 block w-full p-2.5 dark:bg-gray-600 dark:border-gray-500 dark:placeholder-gray-400 dark:text-white"
                placeholder="" type="number" step="0.01" step-my   id="precio_venta" required/>
        </div>
    
    
    <div class="w-2/3">
        <p class="text-gray-700 dark:text-gray-400 m-1.5">Categoría</p>
        <select onchange="changeSelectCategoria()" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-purple-500 focus:border-purple-500 block w-full p-2.5 dark:bg-gray-600 dark:border-gray-500 dark:placeholder-gray-400 dark:text-white"
        id="categoria" required>
    `
    window.objCategorias.forEach(categoria => {
        t += `<option value="${categoria.id}">${categoria.nombre}</option>`
	})
    t += `<select/>
        </div>
    </div>
    
    <div class="max-w-lg">
        <p class="text-gray-700 dark:text-gray-400 m-1.5">Seleccione una imagen</p>
        <div class="flex justify-center items-center w-full my-2">
            <button class="material-icons text-gray-400" onclick="scrollToLeft()">arrow_back_ios</button>
            <ul class="flex w-full p-0.5 space-x-2 overflow-auto scrollbar scrollbar-sm rounded-full" id="scrollContainerImagesProduct" style="">
                <li>
                    <input type="file" accept="image/*" id="image-product" value="image-product" class="hidden peer" onchange="previewImage(event,'product')">
                    <label for="image-product" id="content-image-product" class="inline-flex  w-16 h-16 p-0.5 rounded-full bg-white border-2 border-gray-200 cursor-pointer">
                        <img class="w-14 h-14 bg-purple-600 rounded-full" src="/static/images/add-image2.jpg" alt="" id="preview-image-product">
                    </label>
                </li>
                
                <li>
                    <input type="radio" id="no_image" name="image-product" value="no_image" class="hidden peer" onchange="selectImagenProduct()" checked>
                    <label for="no_image" class="inline-flex w-16 h-16 p-0.5 bg-white border-2 border-gray-200 rounded-full cursor-pointer dark:border-gray-700 dark:peer-checked:text-purple-500 peer-checked:border-purple-600 peer-checked:text-purple-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">  
                        <img class="w-14 h-14 rounded-full" src="/static/images/productos/no_image.jpg" alt="donut">                         
                    </label>
                </li>

                <li>
                    <input type="radio" id="donut" name="image-product" value="donut" class="hidden peer" onchange="selectImagenProduct()">
                    <label for="donut" class="inline-flex w-16 h-16 p-0.5 bg-white border-2 border-gray-200 rounded-full cursor-pointer dark:border-gray-700 dark:peer-checked:text-purple-500 peer-checked:border-purple-600 peer-checked:text-purple-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">  
                        <img class="w-14 h-14 rounded-full" src="/static/images/productos/donut.jpg" alt="donut">                         
                    </label>
                </li>
                <li>
                    <input type="radio" id="french-fries" name="image-product" value="french-fries" class="hidden peer" onchange="selectImagenProduct()">
                    <label for="french-fries" class="inline-flex w-16 h-16 p-0.5 bg-white border-2 border-gray-200 rounded-full cursor-pointer dark:border-gray-700 dark:peer-checked:text-purple-500 peer-checked:border-purple-600 peer-checked:text-purple-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">  
                        <img class="w-14 h-14 rounded-full" src="/static/images/productos/french-fries.jpg" alt="french-fries">                         
                    </label>
                </li>
                <li>
                    <input type="radio" id="pizza" name="image-product" value="pizza" class="hidden peer" onchange="selectImagenProduct()">
                    <label for="pizza" class="inline-flex w-16 h-16 p-0.5 bg-white border-2 border-gray-200 rounded-full cursor-pointer dark:border-gray-700 dark:peer-checked:text-purple-500 peer-checked:border-purple-600 peer-checked:text-purple-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">  
                        <img class="w-14 h-14 rounded-full" src="/static/images/productos/pizza.jpg" alt="pizza">                         
                    </label>
                </li>
                <li>
                    <input type="radio" id="sandwich" name="image-product" value="sandwich" class="hidden peer" onchange="selectImagenProduct()">
                    <label for="sandwich" class="inline-flex w-16 h-16 p-0.5 bg-white border-2 border-gray-200 rounded-full cursor-pointer dark:border-gray-700 dark:peer-checked:text-purple-500 peer-checked:border-purple-600 peer-checked:text-purple-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">  
                        <img class="w-14 h-14 rounded-full" src="/static/images/productos/sandwich.jpg" alt="sandwich">                         
                    </label>
                </li>
                <li>
                    <input type="radio" id="chicken" name="image-product" value="chicken" class="hidden peer" onchange="selectImagenProduct()">
                    <label for="chicken" class="inline-flex w-16 h-16 p-0.5 bg-white border-2 border-gray-200 rounded-full cursor-pointer dark:border-gray-700 dark:peer-checked:text-purple-500 peer-checked:border-purple-600 peer-checked:text-purple-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">  
                        <img class="w-14 h-14 rounded-full" src="/static/images/productos/chicken.jpg" alt="chicken">                         
                    </label>
                </li>
                <li>
                    <input type="radio" id="pudding" name="image-product" value="pudding" class="hidden peer" onchange="selectImagenProduct()">
                    <label for="pudding" class="inline-flex w-16 h-16 p-0.5 bg-white border-2 border-gray-200 rounded-full cursor-pointer dark:border-gray-700 dark:peer-checked:text-purple-500 peer-checked:border-purple-600 peer-checked:text-purple-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">  
                        <img class="w-14 h-14 rounded-full" src="/static/images/productos/pudding.jpg" alt="pudding">                         
                    </label>
                </li>
                <li>
                    <input type="radio" id="ice-cream" name="image-product" value="ice-cream" class="hidden peer" onchange="selectImagenProduct()">
                    <label for="ice-cream" class="inline-flex w-16 h-16 p-0.5 bg-white border-2 border-gray-200 rounded-full cursor-pointer dark:border-gray-700 dark:peer-checked:text-purple-500 peer-checked:border-purple-600 peer-checked:text-purple-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">  
                        <img class="w-14 h-14 rounded-full" src="/static/images/productos/ice-cream.jpg" alt="ice-cream">                         
                    </label>
                </li>
                <li>
                    <input type="radio" id="chocolate" name="image-product" value="chocolate" class="hidden peer" onchange="selectImagenProduct()">
                    <label for="chocolate" class="inline-flex w-16 h-16 p-0.5 bg-white border-2 border-gray-200 rounded-full cursor-pointer dark:border-gray-700 dark:peer-checked:text-purple-500 peer-checked:border-purple-600 peer-checked:text-purple-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">  
                        <img class="w-14 h-14 rounded-full" src="/static/images/productos/chocolate.jpg" alt="chocolate">                         
                    </label>
                </li>
                <li>
                    <input type="radio" id="butter" name="image-product" value="butter" class="hidden peer" onchange="selectImagenProduct()">
                    <label for="butter" class="inline-flex w-16 h-16 p-0.5 bg-white border-2 border-gray-200 rounded-full cursor-pointer dark:border-gray-700 dark:peer-checked:text-purple-500 peer-checked:border-purple-600 peer-checked:text-purple-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">  
                        <img class="w-14 h-14 rounded-full" src="/static/images/productos/butter.jpg" alt="butter">                         
                    </label>
                </li>
                <li>
                    <input type="radio" id="candy" name="image-product" value="candy" class="hidden peer" onchange="selectImagenProduct()">
                    <label for="candy" class="inline-flex w-16 h-16 p-0.5 bg-white border-2 border-gray-200 rounded-full cursor-pointer dark:border-gray-700 dark:peer-checked:text-purple-500 peer-checked:border-purple-600 peer-checked:text-purple-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">  
                        <img class="w-14 h-14 rounded-full" src="/static/images/productos/candy.jpg" alt="candy">                         
                    </label>
                </li>
                <li>
                    <input type="radio" id="apple" name="image-product" value="apple" class="hidden peer" onchange="selectImagenProduct()">
                    <label for="apple" class="inline-flex w-16 h-16 p-0.5 bg-white border-2 border-gray-200 rounded-full cursor-pointer dark:border-gray-700 dark:peer-checked:text-purple-500 peer-checked:border-purple-600 peer-checked:text-purple-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">  
                        <img class="w-14 h-14 rounded-full" src="/static/images/productos/apple.jpg" alt="apple">                         
                    </label>
                </li>
                <li>
                    <input type="radio" id="coffee" name="image-product" value="coffee" class="hidden peer" onchange="selectImagenProduct()">
                    <label for="coffee" class="inline-flex w-16 h-16 p-0.5 bg-white border-2 border-gray-200 rounded-full cursor-pointer dark:border-gray-700 dark:peer-checked:text-purple-500 peer-checked:border-purple-600 peer-checked:text-purple-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">  
                        <img class="w-14 h-14 rounded-full" src="/static/images/productos/coffee.jpg" alt="coffee">                         
                    </label>
                </li>
                <li>
                    <input type="radio" id="juice" name="image-product" value="juice" class="hidden peer" onchange="selectImagenProduct()">
                    <label for="juice" class="inline-flex w-16 h-16 p-0.5 bg-white border-2 border-gray-200 rounded-full cursor-pointer dark:border-gray-700 dark:peer-checked:text-purple-500 peer-checked:border-purple-600 peer-checked:text-purple-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">  
                        <img class="w-14 h-14 rounded-full" src="/static/images/productos/juice.jpg" alt="juice">                         
                    </label>
                </li>
                <li>
                    <input type="radio" id="drink" name="image-product" value="drink" class="hidden peer" onchange="selectImagenProduct()">
                    <label for="drink" class="inline-flex w-16 h-16 p-0.5 bg-white border-2 border-gray-200 rounded-full cursor-pointer dark:border-gray-700 dark:peer-checked:text-purple-500 peer-checked:border-purple-600 peer-checked:text-purple-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">  
                        <img class="w-14 h-14 rounded-full" src="/static/images/productos/drink.jpg" alt="drink">                         
                    </label>
                </li>
                <li>
                    <input type="radio" id="clinking" name="image-product" value="clinking" class="hidden peer" onchange="selectImagenProduct()">
                    <label for="clinking" class="inline-flex w-16 h-16 p-0.5 bg-white border-2 border-gray-200 rounded-full cursor-pointer dark:border-gray-700 dark:peer-checked:text-purple-500 peer-checked:border-purple-600 peer-checked:text-purple-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">  
                        <img class="w-14 h-14 rounded-full" src="/static/images/productos/clinking.jpg" alt="clinking">                         
                    </label>
                </li>
                <li>
                    <input type="radio" id="cocktail" name="image-product" value="cocktail" class="hidden peer" onchange="selectImagenProduct()">
                    <label for="cocktail" class="inline-flex w-16 h-16 p-0.5 bg-white border-2 border-gray-200 rounded-full cursor-pointer dark:border-gray-700 dark:peer-checked:text-purple-500 peer-checked:border-purple-600 peer-checked:text-purple-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">  
                        <img class="w-14 h-14 rounded-full" src="/static/images/productos/cocktail.jpg" alt="cocktail">                         
                    </label>
                </li>
                <li>
                    <input type="radio" id="wine" name="image-product" value="wine" class="hidden peer" onchange="selectImagenProduct()">
                    <label for="wine" class="inline-flex w-16 h-16 p-0.5 bg-white border-2 border-gray-200 rounded-full cursor-pointer dark:border-gray-700 dark:peer-checked:text-purple-500 peer-checked:border-purple-600 peer-checked:text-purple-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">  
                        <img class="w-14 h-14 rounded-full" src="/static/images/productos/wine.jpg" alt="wine">                         
                    </label>
                </li>
                <li>
                    <input type="radio" id="cigar" name="image-product" value="cigar" class="hidden peer" onchange="selectImagenProduct()">
                    <label for="cigar" class="inline-flex w-16 h-16 p-0.5 bg-white border-2 border-gray-200 rounded-full cursor-pointer dark:border-gray-700 dark:peer-checked:text-purple-500 peer-checked:border-purple-600 peer-checked:text-purple-600 hover:text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700">  
                        <img class="w-14 h-14 rounded-full" src="/static/images/productos/cigar.jpg" alt="cigar">                         
                    </label>
                </li>
                   
            </ul>                
            <button class="material-icons text-gray-400" onclick="scrollRight()">arrow_forward_ios</button>
        </div>
    </div>
    </div>
    `

    document.getElementById("content-modal").innerHTML = t;
    const btn_accept = document.getElementById("btn-accept");
    btn_accept.innerText = "Agregar";
    btn_accept.setAttribute("onclick","agregarProducto()")
}

function scrollToLeft() {
    const scrollArea = document.querySelector('#scrollContainerImagesProduct');
    scrollArea.scrollLeft -= 50;
}

function scrollRight() {
    const scrollArea = document.querySelector('#scrollContainerImagesProduct');
    scrollArea.scrollLeft += 50;
}

function changeProductoToSubproducto(v){
    if(v == true){
        document.getElementById("precio_venta").removeAttribute("required")
        document.getElementById("content-options-subproducto").classList.add("hidden");
        var select = document.getElementById("categoria");
        for (var i = 0; i < select.options.length; i++) {
          if (select.options[i].text == "SUBPRODUCTOS") {
            select.options[i].selected = true;
            break;
          }
        }
    }
    else{
        document.getElementById("precio_venta").setAttribute("required","true")
        document.getElementById("content-options-subproducto").classList.remove("hidden");
        var select = document.getElementById("categoria");
        for (var i = 0; i < select.options.length; i++) {
            if (select.options[i].text != "SUBPRODUCTOS") {
                select.options[i].selected = true;
                break;
            }
        }
    }
}

function changeSelectCategoria() {
    var select = document.getElementById("categoria");
    for (var i = 0; i < select.options.length; i++) {
        if (select.options[i].text == "SUBPRODUCTOS" && select.options[i].value == select.value) {
            document.getElementById('add-as-subproducto').checked = true;
            changeProductoToSubproducto(true);
            break;
        }
    }
}


function agregarProducto(){
    let csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
    let categoria = document.getElementById('categoria').value;
    let nombre = document.getElementById('nombre').value;
    let descripcion = document.getElementById('descripcion').value;
    let codigo = document.getElementById('codigo').value;
    let precio_venta = document.getElementById('precio_venta').value;
    let medida = document.getElementById('medida').value;

    if(nombre == "" || nombre == null){
        let alert = document.getElementById("error-add");
        alert.innerHTML = `
        <svg class="w-6 h-6 mr-1" aria-hidden="true" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m0-10.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.75c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.57-.598-3.75h-.152c-3.196 0-6.1-1.249-8.25-3.286zm0 13.036h.008v.008H12v-.008z"></path>
        </svg>
        Proporcione el nombre del producto`;
        alert.classList.remove("hidden");
        return
    }
    if((precio_venta == "" || precio_venta == null) && document.getElementById("add-as-subproducto").checked === false){
        let alert = document.getElementById("error-add");
        alert.innerHTML = `
        <svg class="w-6 h-6 mr-1" aria-hidden="true" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m0-10.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.75c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.57-.598-3.75h-.152c-3.196 0-6.1-1.249-8.25-3.286zm0 13.036h.008v.008H12v-.008z"></path>
        </svg>
        Proporcione el precio de venta del producto`;
        alert.classList.remove("hidden");
        return
    }
    if(medida == "" || medida == null){
        let alert = document.getElementById("error-add");
        alert.innerHTML = `
        <svg class="w-6 h-6 mr-1" aria-hidden="true" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m0-10.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.75c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.57-.598-3.75h-.152c-3.196 0-6.1-1.249-8.25-3.286zm0 13.036h.008v.008H12v-.008z"></path>
        </svg>
        La unidad de medida del producto`;
        alert.classList.remove("hidden");
        return
    }

    loading(true,"Creando Producto")
    
    var formData = new FormData();
    formData.append('categoria', categoria);
    formData.append('nombre', nombre);
    formData.append('descripcion', descripcion);
    formData.append('codigo', codigo);
    formData.append('precio_venta', precio_venta);
    formData.append('medida', medida);
    formData.append('csrfmiddlewaretoken', csrf);

    var fileInput = document.getElementById('image-product');
    if (fileInput.files && fileInput.files[0]) {
        formData.append('image-product', fileInput.files[0]);
    }
    else{
        var radios = document.getElementsByName('image-product');
        for (var i = 0; i < radios.length; i++) {
          if (radios[i].checked) {
            formData.append('image-product', radios[i].value);
            break;
          }
        }
    }

    $.ajax({
        url:"/config-add-producto/",
        type:"post",
        data:formData,
        processData: false,
        contentType: false,
        success:function(response){
            loading(false)
            document.querySelector('[name=csrfmiddlewaretoken]').value = response.csrf;

            if(response.register == "success"){
                let content = document.getElementById("body-productos");
                const button = document.createElement('button');
                button.className = "item-product flex px-4 py-3 hover:bg-gray-100 dark:hover:bg-gray-700 w-full";
                button.id=`product-${response.new_producto.id}`;
                button.setAttribute("onclick",`addProduct(${response.new_producto.id},'${response.new_producto.nombre}','${response.new_producto.medida}','${codigo}',0)`);
                button.innerHTML = `
                <div class="flex-shrink-0">
                  <img class="rounded-full w-11 h-11" src="${response.new_producto.imagen}" alt="">
                </div>
                <div class="w-full pl-3 flex flex-col">
                    <span id="name-product-${response.new_producto.id}" class="text-gray-900 font-bold text-md dark:text-gray-400 text-start">${response.new_producto.nombre}</span>
                    <span class="text-gray-500 text-sm mb-0.5 dark:text-gray-400 text-start"${descripcion}</span>
                    <span class="text-xs text-blue-600 dark:text-blue-500 text-start">${response.new_producto.medida}</span>
                </div>
                `;
                content.appendChild(button);
                document.getElementById("btn-cancel").click();
            }
            else if(response.register == "exist"){
                let alert = document.getElementById("error-add");
                alert.innerHTML = `
                <svg class="w-6 h-6 mr-1" aria-hidden="true" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m0-10.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.75c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.57-.598-3.75h-.152c-3.196 0-6.1-1.249-8.25-3.286zm0 13.036h.008v.008H12v-.008z"></path>
                </svg>
                Ya existe el producto  ${nombre}`;
                alert.classList.remove("hidden");
            }
            else if(response.register == "error"){
                let alert = document.getElementById("error-add");
                alert.innerHTML = `
                <svg class="w-6 h-6 mr-1" aria-hidden="true" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m0-10.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.75c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.57-.598-3.75h-.152c-3.196 0-6.1-1.249-8.25-3.286zm0 13.036h.008v.008H12v-.008z"></path>
                </svg>
                Error al agregar producto`;
                alert.classList.remove("hidden");
            }
        },
        error:function(response){
            loading(false)
            let alert = document.getElementById("error-add");
            alert.innerHTML = `
            <svg class="w-6 h-6 mr-1" aria-hidden="true" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m0-10.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.75c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.57-.598-3.75h-.152c-3.196 0-6.1-1.249-8.25-3.286zm0 13.036h.008v.008H12v-.008z"></path>
            </svg>
            Error al agregar producto`;
            alert.classList.remove("hidden");
        },
    });
}

function loading(v,t=""){
    if(v){
        document.getElementById("loading").classList.remove("hidden");
        document.getElementById("content-options").classList.add("hidden");
        document.getElementById("text-loadding").innerText = t;
    }
    else{
        document.getElementById("loading").classList.add("hidden");
        document.getElementById("content-options").classList.remove("hidden");

    }
}

function previewImage(event,content_id) {
    var input = event.target;
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function(e) {
            var preview = document.getElementById(`preview-image-${content_id}`);
            preview.src = e.target.result;
        }
        reader.readAsDataURL(input.files[0]);

        if(content_id == "user"){
            document.getElementById("women-user").checked = false;
            document.getElementById("men-user").checked = false;            
            document.getElementById(`content-image-${content_id}`).className = "inline-flex w-25 h-25 p-0.5 rounded-full bg-white border-2 border-purple-600 cursor-pointer";
        }
        else if(content_id == "product"){
            if(getImagenProducto()){getImagenProducto().checked = false;}
            document.getElementById(`content-image-${content_id}`).className = "inline-flex w-16 h-16 p-0.5 rounded-full bg-white border-2 border-purple-600 cursor-pointer";
        }

    }
}

function selectImagenProduct() {
    var preview = document.getElementById('preview-image-product');
    preview.src = "/static/images/add-image2.jpg";

    document.getElementById("content-image-product").className = "inline-flex w-16 h-16 p-0.5 rounded-full bg-white border-2 border-gray-200 cursor-pointer";
}


function changeSelectCategoria() {
    var select = document.getElementById("categoria");
    for (var i = 0; i < select.options.length; i++) {
        if (select.options[i].text == "SUBPRODUCTOS" && select.options[i].value == select.value) {
            document.getElementById('add-as-subproducto').checked = true;
            changeProductoToSubproducto(true);
            break;
        }
    }
}