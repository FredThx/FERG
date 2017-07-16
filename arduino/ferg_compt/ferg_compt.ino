/***************************************************************************
 * Projet : FERG
 *          Vieux compteur EDF connecte
 * *************************************************************************
 *      Il s'agit ici de lire un capteur optique 
 *      placé devant la roue du compteur EDF. Et de renvoir 
 *      à un rasperry pi via i2c le nb de tours detectés
 * 
 *      l'arduino (ou atmega328) est en mode esclave
 *        quand il reçoit une demande de lecture, il renvoie le nb de tours 
 *        detecte depuis la derniere demande.
 * 
 *      A l'initialisation, il scan le capteur pour determiner le seuil de déclenchement.
 *      S'il reçoit via i2c la commande RESET = "88", il relance ce calcul.
 ****************************************************************************
 * Auteur : FredThx
 * Date : 15/11/2015
 * **************************************************************************
 */



#include <Wire.h>
#define MY_I2C_ADDR 0x12// Adresse i2c
#define LED 8           // led pour visualiser la detection
#define CAPTEUR 0       // Capteur sur l'entree analogique 'A0'
#define INTERVAL_MES 7  // en milisecondes entre 2 mesures
#define DURATION 20     // Durée minimum en millisecondes pour  valider un detection
#define TIMEOUT 60      // Nb de secondes du tour le plus lent
#define RESET 88        // Ordre de reset



/*
 * Variables Globales
 */
unsigned short int nb_tours = 0;
int seuil_bande ;
unsigned long time_last_detect;
bool on_setup ; // définit s'il faut calculer le seuil de detection (true) ou mesurer (false)

/*
 * Initialisation
 */
void setup() {
    Serial.begin(9600);
    on_setup = true;
	  Wire.begin(MY_I2C_ADDR);
    Wire.onReceive(receiveData);
    Wire.onRequest(sendData);
    pinMode(LED,OUTPUT);
    led_off();
    on_setup = true;
    time_last_detect = millis();
}

/*
 * Main
 *  lecture du capteur 
 *    si le voltage dépasse le seuil plus longtemps que DURATION
 *    on compte un tour de plus.
 */
void loop() {
	if (on_setup){
    seuil_bande = mesure_seuil();
	}else{
	   unsigned long t0;
	   unsigned long t1;
	   t0 = millis();
	   t1 = millis();
	   while ((analogRead(CAPTEUR)> seuil_bande) and ((t1 - t0 < TIMEOUT * 50))){
		  t1 = millis();
	   }
	   if ((t1 - t0 >= TIMEOUT * 500)){
		    //Si timeout, on recalcul de seuil de detection (qui doit ,être trop bas)
        Serial.println("Bande noire trop longue. Le seuil doit etre trop bas.");
		    nb_tours = 201;
		    on_setup = true;
		    t1 = millis();
		    time_last_detect = t1;
	   }else{
		    if ((t1-t0)>DURATION){
			    led_on();
			    nb_tours +=1;
			    delay(INTERVAL_MES * 10);
			    time_last_detect = t1;
		      led_off();
		    }
	   }
	   if ((t1 - time_last_detect) > TIMEOUT * 2000){
		    //Si timeout, on recalcul de seuil de detection (qui doit ,être trop haut)
        Serial.println("Pas de detection dans le temps imparti. Le seuil doit etre trop haut");
		    on_setup = true;
		    time_last_detect = millis();
	   }
	  delay(INTERVAL_MES);
	}
}


/*
 * Deamon sur reception de donnees via i2c
 *    Si reception de RESET : recalcul du seuil
 */
void receiveData(int byteCount){
    int dataReceived;
    Serial.println("Donnees recues du serveur i2c.");
    while(Wire.available()) {
        dataReceived = Wire.read();
        if (dataReceived == RESET){
          Serial.println("Initialisation demandee par le Serveur i2c.");
          nb_tours = 0;
          on_setup = true; //demande un recalcul du seuil de detection
        }
    }
}

/*
 * Deamon sur demande de donnees via i2c
 */
void sendData(){
	if (not on_setup){
		unsigned short int nb_tours_to_send = 0;
		if (nb_tours > 0){
		  if (nb_tours < 255){
			nb_tours_to_send = nb_tours;
		  } else{
			nb_tours_to_send = 255;
		  }
		  nb_tours -= nb_tours_to_send;
     Serial.print("i2c_write : ");
     Serial.println(nb_tours_to_send);
		  Wire.write(nb_tours_to_send);
		}
	} else {
		Wire.write(0);
	}
}

/*
 * Mesure du seuil de detection
 *    quand la bande noire passe devant le capteur, le voltage augmente
 *    ici, on determine le seuil de detection
 */
int mesure_seuil(){
  //Mesure pendant TIMEOUT secondes
  Serial.println("Calcul du seuil de detection de bande noire.");
  int maxi;
  double moyenne;
  int mesure;
  int i = 0;
  unsigned long t0;
  unsigned long t1;
  unsigned long pause;
  led_on();
  t0 = millis();
  t1 = millis();
  maxi = analogRead(CAPTEUR),
  moyenne = analogRead(CAPTEUR);
  while (((t1-t0)/1000 < TIMEOUT) and (t0<=t1)){
    mesure = analogRead(CAPTEUR);
    maxi = max(maxi, mesure);
    moyenne = moyenne*i + mesure;
    i++;
    moyenne /= i;
    //Serial.print("Maxi :");
    //Serial.print(maxi);
    //Serial.print(" Moyenne :");
    //Serial.print(int(moyenne));
    Serial.print(" mesure(");
    Serial.print(i);
    Serial.print(") : ");
    Serial.println(mesure);
    //Serial.print(" . temps :");
    //Serial.println(int((t1-t0)/1000));
    t1 = millis();
  }
  led_off();
  on_setup = false;
  Serial.print("Seuil mesure : ");
  Serial.println(moyenne + (maxi - moyenne)*0.75);
  Serial.print("Pour une moyenne de : ");
  Serial.println(moyenne);
  return moyenne + (maxi - moyenne)*0.75;
}

/*
 * Gestion de la LED
 */
void led_on(){
  digitalWrite(LED,HIGH);
}

void led_off(){
  digitalWrite(LED,LOW);
}

