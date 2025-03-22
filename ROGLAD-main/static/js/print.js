
function print(head,html) {
    let ventimp = window.open(' ', 'popimpr');
    let htmlPass = `<head>${head}</head>` + html.replace("shadow-","") +
    `<script>
        const elementos = document.querySelectorAll('[add-class-print]');
        elementos.forEach(elemento => {
            elemento.className += ' ' + elemento.getAttribute('add-class-print');
        });

        const elementosNoPrint = document.querySelectorAll('.no-print');
        elementosNoPrint.forEach(elemento => {
            elemento.remove();
        });
        
        setTimeout(function(){
            window.print();
            window.close();
        }, 500);
    </script>
    `;
    ventimp.document.write( htmlPass );
  }