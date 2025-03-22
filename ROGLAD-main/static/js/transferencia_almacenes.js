function changeCantRemitida(id,precio){
    let input = document.getElementById(`cantiad-${id}`);
    //input.value = parseFloat(input.value);

    if( input.value < parseFloat(input.getAttribute("min")) ){
        input.value = input.getAttribute("min");
    }
    else if( input.value > parseFloat(input.getAttribute("max")) ){
        input.value = input.getAttribute("max");
    }
    let precio_total = (input.value * precio).toString();
    document.getElementById(`precio-start-${id}`).textContent = precio_total.split(".")[0];
    var pte = precio_total.split(".")[1];
    if( !pte ){ pte = "00";}
    else if( pte.length == 1){pte += "0";}
    document.getElementById(`precio-end-${id}`).textContent = pte;
    var valorPrevio = input.getAttribute('value-previus');

    let val_cant = input.value;
    if(val_cant == ""){val_cant = 0;}

    let existencia_element = document.getElementById(`existencia-${id}`)
    var existencia = parseFloat(existencia_element.textContent) + parseFloat(valorPrevio) - parseFloat(val_cant);
    
    if( existencia.toString() == "NaN" ){
        existencia = existencia_element.getAttribute("existencia-almacen");
    }

    existencia_element.textContent = existencia;

    var importe_total = parseFloat(document.getElementById("importe-total-start").textContent + "." + document.getElementById("importe-total-end").textContent);
    var importe_total_new = (importe_total - (valorPrevio * precio) + (val_cant * precio)).toFixed(2).toString();

    
    
    document.getElementById(`importe-total-start`).textContent = importe_total_new.split(".")[0];
    
    var ite = importe_total_new.split(".")[1];
    if( !ite ){ ite = "00";}
    else if( ite.length == 1){ite += "0";}
    document.getElementById(`importe-total-end`).textContent = ite;
    input.setAttribute('value-previus',val_cant);


}

function addProduct(id,lote_asignar,existencia,codigo,nombre,medida,precio_venta,categoria=""){
    
    const elemento = document.getElementById(`producto-transferir-${id}`);
    if (elemento) { return }
        
    document.getElementById("input-search").focus()
    document.getElementById("input-search").select()
    var precio_venta_list = precio_venta.toString().split(".")
    if(precio_venta_list.length == 1 ){
        precio_venta_list.push("00")
    }
    let content = document.getElementById("content-products");

    const newProduct = document.createElement('div');
    newProduct.id = `product-content-${id}`;
    newProduct.innerHTML = `
    <input type="number" step="0.01" step-my  name="lote-id" class="hidden" value="${lote_asignar}" id="producto-transferir-${id}">
    <input type="number" step="0.01" step-my  name="productos-ids" class="hidden" value="${id}" required>
    <div class="flex w-1/3">
        <div class="w-2/5 border h-full text-sm text-center flex items-center justify-between">
            <button type="button" class="text-red-500 px-1 material-icons text-md" onclick="removedProduct(${id})">delete_outline</button>
            <span class="w-full text-start flex items-center">${codigo}</span>
        </div>
        <span class="w-2/5 border h-full text-sm text-center flex items-center justify-center" name="name-product-transfer" categoria="${categoria}">${nombre}</span>
        <span class="w-1/5 border h-full text-sm text-center flex items-center justify-center">${medida}</span>
    </div>
    <div class="flex w-1/3">
        <div class="flex w-1/2 h-full">
            <div class="flex w-1/2 border">
                <span class="text-red-700 mr-2">*</span>
                <input type="number" step="0.01" step-my  id="cantiad-${id}" name="cantidad" step="0.01" class="item-form bg-transparent border-0 text-md  block w-full p-0.5 focus:ring-0 appearance-none focus:outline-none focus:ring-0 " 
                oninput="changeCantRemitida(${id},${precio_venta})"
                min=0 max=${existencia} value-previus=0  required>
            </div>
            <span class="w-1/2 border h-full text-sm text-center flex items-center justify-center">-</span>
        </div>
        <div class="flex w-1/2 h-full">
            <span class="w-2/3 border h-full text-sm text-center flex items-center justify-center">${precio_venta_list[0]}</span>
            <span class="w-1/3 border h-full text-sm text-center flex items-center justify-center">${precio_venta_list[1]}</span>
        </div>
    </div>
    <div class="flex w-1/3">
        <div class="flex w-2/3 h-full">
            <div class="flex w-1/2 h-full">
                <span class="w-2/3 border h-full text-sm text-center flex items-center justify-center" id="precio-start-${id}">0</span>
                <span class="w-1/3 border h-full text-sm text-center flex items-center justify-center" id="precio-end-${id}">00</span>
            </div>
            <div class="flex w-1/2 h-full">
                <span class="w-2/3 border h-full text-sm text-center flex items-center justify-center">-</span>
                <span class="w-1/3 border h-full text-sm text-center flex items-center justify-center">-</span>
            </div>
        </div>
        <span id="existencia-${id}" class="w-1/3 border h-full text-sm text-center flex items-center justify-center" existencia-almacen=${existencia}>${existencia}</span>
    </div>`;
    newProduct.className = "flex";

    content.appendChild(newProduct);
    document.getElementById("product-"+id).classList.add("hidden");
    document.getElementById("product-"+id).classList.add("product-select");
    //document.getElementById("close-modal-products").click();
}

function removedProduct(id){
    
    var importe_eliminado = parseFloat(document.getElementById("precio-start-"+id).textContent + "." + document.getElementById("precio-end-"+id).textContent);
    var importe_total = parseFloat(document.getElementById("importe-total-start").textContent + "." + document.getElementById("importe-total-end").textContent);
    var importe_total_new = (importe_total - importe_eliminado).toString();
    
    document.getElementById(`importe-total-start`).textContent = importe_total_new.split(".")[0];
    console.log(importe_total_new)
    var ite = importe_total_new.split(".")[1];
    if( !ite ){ ite = "00";}
    else if( ite.length == 1){ite += "0";}
    document.getElementById(`importe-total-end`).textContent = ite;
    
    document.getElementById(`product-content-${id}`).remove();
    document.getElementById("product-"+id).classList.remove("hidden");
    document.getElementById("product-"+id).classList.remove("product-select");
}

function search(){
    var elements = document.getElementsByClassName("item-product");
    for (var i = 0; i < elements.length; i++) {
        if (!elements[i].classList.contains("product-select")) {
            var inputText = document.getElementById("input-search").value.toLowerCase();
            var nameText = document.getElementById(`name-${elements[i].id}`).textContent.toLowerCase();
            var codeText = document.getElementById(`code-${elements[i].id}`).textContent.toLowerCase();
            
            
            if (nameText.includes(inputText) || codeText.includes(inputText)) {
                elements[i].classList.remove("hidden");
            } else {
                elements[i].classList.add("hidden");
            }
        }
    }
}