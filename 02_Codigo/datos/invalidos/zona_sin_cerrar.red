RED campus {
    DISPOSITIVO Router1 router 192.168.1.1 ;
    ZONA datacenter {
        DISPOSITIVO Server servidor 192.168.1.10 ;
        ENLACE Router1 Server 3 ;
