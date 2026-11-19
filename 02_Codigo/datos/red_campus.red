# Red con zonas anidadas (sección 11 del documento): 3 niveles de bloques
RED campus {
    DISPOSITIVO Router1 router 192.168.1.1 ;
    ZONA datacenter {
        DISPOSITIVO Switch2 switch 192.168.1.3 ;
        DISPOSITIVO Server servidor 192.168.1.10 ;
        ZONA rack1 {
            DISPOSITIVO DB servidor 192.168.1.11 ;
        }
        ENLACE Switch2 Server 1 ;
        ENLACE Server DB 2 ;
    }
    ENLACE Router1 Switch2 3 ;
}
