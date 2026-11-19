# La red completa del laboratorio descrita con zonas
RED laboratorio {
    DISPOSITIVO Router1 router 192.168.1.1 ;
    ZONA aula {
        DISPOSITIVO Switch1 switch 192.168.1.2 ;
        DISPOSITIVO PC1 pc 192.168.1.21 ;
        DISPOSITIVO PC2 pc 192.168.1.22 ;
        DISPOSITIVO Impresora1 pc 192.168.1.30 ;
        ENLACE Switch1 PC1 1 ;
        ENLACE Switch1 PC2 1 ;
    }
    ZONA datacenter {
        DISPOSITIVO Switch2 switch 192.168.1.3 ;
        ZONA rack1 {
            DISPOSITIVO Server servidor 192.168.1.10 ;
            DISPOSITIVO DB servidor 192.168.1.11 ;
            ENLACE Server DB 2 ;
        }
        ENLACE Switch2 Server 1 ;
    }
    ENLACE Router1 Switch1 2 ;
    ENLACE Router1 Switch2 3 ;
    ENLACE PC2 DB 4 ;
}
