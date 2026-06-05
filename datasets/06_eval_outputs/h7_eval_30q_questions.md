# H7 Evaluation Set (30 Questions)

## Issues-Centric (Q01-Q10)

Q01. Pourquoi CubeMX garde TX et RX assignes quand USART est en receive-only sur STM32H7 ?

Q02. Comment configurer correctement Conversion Data Management pour ADC + DMA sur STM32H743 ?

Q03. Quelles causes probables expliquent un echec de synchronisation CM7/CM4 sur H747 ?

Q04. Pourquoi CM4 peut ne pas sortir de STOP avec notification HSEM sur dual-core H7 ?

Q05. Comment traiter proprement les warnings -Wcast-align dans HAL UART / ethernetif sur H7 ?

Q06. COM1 mappe sur USART3 sur NUCLEO-H753ZI: bug ou comportement attendu ?

Q07. Comment diagnostiquer FR_NOT_READY avec SDMMC1 + MDMA + FatFs + FreeRTOS sur H7 ?

Q08. Comment respecter les limites datasheet pour ADC clock + BOOST sur STM32H723 ?

Q09. Comment debugger un wakeup standby H747 ou CM7 continue l'execution au lieu de reset ?

Q10. Quelle sequence d'initialisation LL est recommandee pour la calibration ADC sur H7 ?

## Files-Centric (Q11-Q20)

Q11. Dans le README STM32CubeH7, quelle est la bonne commande pour cloner avec tous les submodules ?

Q12. Comment recuperer les dernieres mises a jour du repo deja clone selon le README ?

Q13. D'apres le README, comment se placer sur une version firmware precise vX.Y.Z ?

Q14. Quels middlewares ne sont pas inclus dans le repo GitHub et ou les trouver ?

Q15. Le README indique-t-il une difference possible entre la version GitHub et la version st.com ?

Q16. Quelle est la liste des principaux types de projets fournis dans STM32CubeH7 (examples/applications/demos) ?

Q17. Ou trouver les notes de version de STM32CubeH7 a partir de la documentation du repo ?

Q18. Quelles cartes NUCLEO/EVAL/DK sont mentionnees dans la section Boards available du README H7 ?

Q19. Quelle est la recommandation du README si on utilise Download ZIP au lieu de git clone ?

Q20. Quelle est la difference d'usage entre git clone --recursive et git clone --recursive --depth 1 --branch vX.Y.Z ?

## Mixed (Issues + Files) (Q21-Q30)

Q21. Je veux corriger un bug CubeMX USART single-line sur H7: quelle verification issue faire et quelle version/tag firmware utiliser pour reproduire proprement ?

Q22. Pour un probleme ADC + DMA sur H743, quelle regle de config issue appliquer et quel chemin projet README suivre pour tester sur une board H7 ?

Q23. J'ai un cas FR_NOT_READY SDMMC1: quelle piste issue prioritaire verifier et quelle documentation de release consulter pour valider les changements ?

Q24. Pour un wakeup standby dual-core instable, quels checks techniques issus des tickets et quelles precautions de version firmware du README faut-il combiner ?

Q25. En presence de warnings -Wcast-align, quelle strategie de correction issue recommander et comment aligner cela avec les contraintes de code genere STM32Cube ?

Q26. Je dois reproduire un bug H7 rapporte sur GitHub: quelle methode de checkout version depuis README et quels elements de contexte issue dois-je conserver ?

Q27. Pour un diagnostic UART/USART sur NUCLEO-H753ZI, quelle info board du README et quelle info de mapping issue relier dans la reponse ?

Q28. Si une reponse propose une correction, comment verifier qu'elle est coherente a la fois avec un ticket H7 et avec les instructions d'usage du repo ?

Q29. Comment construire une procedure de debug robuste qui cite une source issue technique et une source file documentaire sans contradiction ?

Q30. Pour reduire les hallucinations, quelle bonne pratique de reponse impose de croiser evidence issue (cas concret) et evidence file (guide officiel) ?
