
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

function calcularPago(){
    let sumPago = parseInt(document.getElementById("bill-1").value) +
    (parseInt(document.getElementById("bill-3").value) * 3) +
    (parseInt(document.getElementById("bill-5").value) * 5) +
    (parseInt(document.getElementById("bill-10").value) * 10) +
    (parseInt(document.getElementById("bill-20").value) * 20) +
    (parseInt(document.getElementById("bill-50").value) * 50) +
    (parseInt(document.getElementById("bill-100").value) * 100) +
    (parseInt(document.getElementById("bill-200").value) * 200) +
    (parseInt(document.getElementById("bill-500").value) * 500) +
    (parseInt(document.getElementById("bill-1000").value) * 1000) 
    
    let item = document.getElementById("btn-cuadrar-turno");
    if(monto_caja == sumPago){
        item.className = "w-full text-white bg-purple-600 hover:bg-purple-800 focus:ring-4 focus:outline-none focus:ring-purple-300 dark:focus:ring-purple-800 font-medium rounded-lg text-sm items-center px-5 py-2.5 text-center ml-2";
        item.setAttribute("type","submit")
    }
    else{
        item.className = "w-full text-gray-600 bg-purple-300 font-medium rounded-lg text-sm items-center px-5 py-2.5 text-center ml-2";
        item.setAttribute("type","button")
    }
}
