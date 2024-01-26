library(plumber)
library(TAM)
library(RPostgres)
library(DBI)
library(dotenv)
library(readxl)

route <- "./data/"
# load_dot_env(".env")

db <- Sys.getenv('DB')
user <- Sys.getenv('DB_USER')
passwd <- Sys.getenv('DB_PASS')
host <- Sys.getenv('DB_HOST')
port <- Sys.getenv('DB_PORT')

# Formato de salida
formato <- read_excel(paste0(route, 'Formato.xlsx'))

#* @get /calibrar
#* @parser json
function(req, table_name="") {
  
  # Carga de la tabla de Postgres
  conn <- dbConnect(RPostgres::Postgres(),
                    dbname=db,
                    host=host,
                    port=port,
                    user=user,
                    password=passwd
                    )
  
  df <- dbReadTable(conn, table_name)
  
  grado <- df$grado %>% unique()
  asignatura <- df$instrumento %>% unique()
  df <- df %>% select(-c('grado', 'instrumento', 'index'))
  df <- df %>% mutate(across(everything(), as.numeric))

  # Calibration
  calibracion1 <- tam(df)
  calibracion2 <- tam.mml.2pl(df)
  calibracion3 <- tam.mml.3pl(df, est.guess = 1:length(calibracion1$item$item))

  # Salida
  lformato <- as.data.frame(matrix(data = NA, nrow = dim(calibracion2$item)[1], ncol = dim(formato)[2]))
  names(lformato) <- names(formato)

  lformato$id_item <- calibracion2$item$item
  lformato$n <- calibracion2$item$N
  lformato$dif_tct <- calibracion2$item$M*100
  lformato$campo <- grado

  # Discriminacion TCT
  for (i in 1:dim(df)[2]) {
    lformato$dis_tct[i] <- cor(df[,i], rowSums(df) - df[,i], use = "na.or.complete")
  }

  ## Dificultad y discriminacion TRI
  lformato$dif_tri <- calibracion2$item_irt$beta
  lformato$dis_tri <- calibracion2$item_irt$alpha

  # Dictamenes
  lformato$dic_dif_tct <- ifelse(lformato$dif_tct < 10 | lformato$dif_tct > 90, "Revisión","Útil")
  lformato$dic_dis_tct <- ifelse(lformato$dis_tct < 0.15, "Revisión","Útil")
  lformato$dic_dif_tri <- ifelse(lformato$dif_tri < (-3) | lformato$dif_tri > 3, "Revisión","Útil")
  lformato$dic_dis_tri <- ifelse(lformato$dis_tri < 0.40 | lformato$dis_tri > 2.8, "Revisión","Útil")
  lformato$dic_tct <- ifelse(lformato$dic_dif_tct == "Útil" & lformato$dic_dis_tct == "Útil", "Útil","Revisión")
  lformato$dic_tri <- ifelse(lformato$dic_dif_tri == "Útil" & lformato$dic_dis_tri == "Útil", "Útil","Revisión")
  lformato$dic_tct_tri <- ifelse(lformato$dic_tct == "Útil" & lformato$dic_tri == "Útil", "Útil","Revisión")

  # Parametros 3PL
  lformato$dif_3pl <- calibracion3$item_irt$beta
  lformato$dis_3pl <- calibracion3$item_irt$alpha
  lformato$adi_3pl <- calibracion3$item$guess

  # Dictamenes 3PL
  lformato$dic_dif_3pl <- ifelse(lformato$dif_3pl < (-3) | lformato$dif_3pl > 3,"Revisión", "Útil")
  lformato$dic_dis_3pl <- ifelse(lformato$dis_3pl < 0.40 | lformato$dis_3pl > 2.8, "Revisión", "Útil")
  lformato$dic_tri_3pl <- ifelse(lformato$dic_dif_3pl == "Útil" & lformato$dic_dis_3pl == "Útil", "Útil", "Revisión")

  # Probs
  lformato$prob_2pl <- 1/(1+exp(-lformato$dis_tri * (0 - lformato$dif_tri)))
  lformato$prob_3pl <- lformato$adi_3pl + (1 - lformato$adi_3pl) / (1 + exp(-lformato$dis_tri*(0 - lformato$dif_tri)))

  # Parametros 1PL
  lformato$dif_1pl <- calibracion1$item_irt$beta
  lformato$prob_1pl <- 1/(1 + exp(-(0 - lformato$dif_1pl)))

  lformato$materia <- asignatura

  result <- lformato
   
  # TODO debe escribir en la base de resultados y devolver mensaje de fin de proceso
  # return(toJSON(result))

}
