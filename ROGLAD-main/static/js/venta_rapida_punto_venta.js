
function upInput(id){
    document.getElementById(id).value = parseInt(document.getElementById(id).value) + 1;
    calcularPago();
}

function downInput(id){
    let element = document.getElementById(id);
    if(parseInt(element.value) > 0){
        element.value = parseInt(element.value) - 1;
        calcularPago();
    }
}

function upInputVenta(){
    let inp = document.getElementById("cant-product-add");
    inp.value = parseInt(inp.value) + 1;
    calcularMontoVenta()
}

function downInputVenta(){
    let inp = document.getElementById("cant-product-add");
    if(parseInt(inp.value) > 1){
        inp.value = parseInt(inp.value) - 1
    }
    calcularMontoVenta()
}


function upInputCantidadVendida(id){
    let inp = document.getElementById(`cantidad-venta-${id}`);
    
    if(parseInt(inp.value) < parseInt(inp.getAttribute("max"))){
        inp.value = parseInt(inp.value) + 1;
        actualizarVenta(id)
    }
}

function downInputCantidadVendida(id){
    let inp = document.getElementById(`cantidad-venta-${id}`);
    if(parseInt(inp.value) > 1){
        inp.value = parseInt(inp.value) - 1
    }
    actualizarVenta(id)
}

function cantidadCambiada(id){
    let inp = document.getElementById(`cantidad-venta-${id}`);
    if(parseInt(inp.value) > parseInt(inp.getAttribute("max"))){
        inp.value = inp.getAttribute("max");
        actualizarVenta(id)
    }
    else if(parseInt(inp.value) < 1){
        inp.value = 1;
        actualizarVenta(id)
    }
    else{
        actualizarVenta(id)
    }
}


function toMoney(m) {
    var monto_list = m.toString().split(".");
    if (monto_list.length == 2){
        if(monto_list[1].length > 1){
            return `$${monto_list[0]}.${monto_list[1]}`;
        }
        else{
            return `$${monto_list[0]}.${monto_list[1]}0`;
        }

    }
    else{
        return `$${monto_list[0]}.00`;
    }
}

function cerrarCuenta(){
    let monto = document.getElementById("monto-total-ventas").innerText.replace("MONTO TOTAL: $","");
    document.getElementById("monto-total-liquidar").innerText = `$${monto}`;
    document.getElementById("resultado-liquidar").innerHTML = `<span class="material-icons">report_problem</span> Falta por liquidar: $${monto}`;
    document.getElementById("resultado-liquidar").className = "flex justify-center font-bold text-md pb-5 text-red-700 dark:text-red-100";
    document.getElementById("btn-liquidar").classList.add("hidden");
    
    document.getElementById("close-cuenta").setAttribute("action",`/punto-venta/${getCuentaValue()}`);
}

function realizarVenta(){
    document.getElementById("cuenta-name").value = "";
    document.getElementById("form-venta-rapida").submit()
}

function getCuentaValue(){
    var cuentas_ids = document.getElementsByName('id-cuenta');
    for (var i = 0; i < cuentas_ids.length; i++) {
      if (cuentas_ids[i].checked) {
        return cuentas_ids[i].value;
      }
    }
}




function agregarNumPago(num){
    let inp = document.getElementById("bill");
    inp.value = inp.value + num;
    calcularPago()
}

function sumarNumPago(num){
    let inp = document.getElementById("bill");
    var cant = inp.value;
    if(cant === ""){cant = 0.0}
    else{cant = parseFloat(cant)}
    inp.value =  cant + parseFloat(num);
    calcularPago()
}

function agregarPunto(){
    let inp = document.getElementById("bill");
    if(!inp.value.toString().includes(".")){
        inp.value = inp.value.toString() + ".";
        calcularPago()
    }
}

function borrarNumPago(){
    let inp = document.getElementById("bill");
    inp.value = inp.value.slice(0, -1);
    calcularPago()
}

function calcularPago(){
    let montoPagar = parseFloat(document.getElementById("monto-total-liquidar").innerText.replace("$","").replace(" CUP",""));
    var sumPago = document.getElementById("bill").value;
    if(sumPago == ""){
        sumPago = 0.0;
    }
    else{
        sumPago = parseFloat(sumPago)
    }
    
    if(montoPagar > sumPago){
        document.getElementById("resultado-liquidar").innerHTML = `<span class="material-icons">report_problem</span> Falta por liquidar: $${montoPagar-sumPago}`;
        document.getElementById("resultado-liquidar").className = "flex justify-center font-bold text-md pb-5 text-red-700 dark:text-red-100";
        document.getElementById("btn-liquidar").classList.add("hidden");
    }
    else if(montoPagar == sumPago){
        document.getElementById("resultado-liquidar").innerHTML = `<span class="material-icons">check_circle</span> Liquidación correcta y sin devolución`;
        document.getElementById("resultado-liquidar").className = "flex justify-center font-bold text-md pb-5 text-green-700 dark:text-green-100";
        document.getElementById("btn-liquidar").classList.remove("hidden");
    }
    else{
        document.getElementById("resultado-liquidar").innerHTML = `<span class="material-icons">notification_important</span> Debe devolver: $${sumPago-montoPagar}`;
        document.getElementById("resultado-liquidar").className = "flex justify-center font-bold text-md pb-5 text-orange-700 dark:text-orange-100";
        document.getElementById("btn-liquidar").classList.remove("hidden");
    }
}

function eliminarVenta(id){
    let inp = document.getElementById(`cantidad-venta-${id}`);    
    inp.value = 0;
    actualizarVenta(id,true);
    document.getElementById(`content-producto-id-${id}`).classList.remove("hidden");
    
    var trElement = document.getElementById(`venta-${id}`);
    if (trElement) {
        trElement.parentNode.removeChild(trElement);
    }
}


function calcularMontoTotal(){
    var monto = 0.0;

    var montoElements = document.getElementsByClassName("monto-venta");
    for (var i = 0; i < montoElements.length; i++) {
        monto += parseFloat(montoElements[i].textContent.replace("$",""));
    }
    
    let monto_total_obj  = document.getElementById("monto-total-ventas");
    monto_total_obj.innerText = `MONTO TOTAL: ${toMoney(monto)}`;

    if(monto == 0.0){
        document.getElementById("content-btns-venta").classList.add("hidden");
    }else{
        document.getElementById("content-btns-venta").classList.remove("hidden");
    }
}

function search(){
    var elements = document.getElementsByClassName("item-product");
    for (var i = 0; i < elements.length; i++) {
        if (!elements[i].classList.contains("product-hidden")) {
            var inputText = document.getElementById("input-search").value.toLowerCase();
            try{
            var nameText = document.getElementById(`${elements[i].id}`.replace("content","name")).textContent.toLowerCase();
            
            if (nameText.includes(inputText)) {
                elements[i].classList.remove("hidden");
            } else {
                elements[i].classList.add("hidden");
            }
            }
            catch{
                elements[i].classList.add("hidden");
            }
        }
    }
}

function clearInput(){
    document.getElementById("input-search").value = ""
    search()
}

function convertirEnCuenta(){
    document.getElementById("cuenta-name").value = document.getElementById("nombre-crear-cuenta").value;
    document.getElementById("form-venta-rapida").submit()
}
