# rodar pip install -r requirements.txt
from selenium import webdriver
from selenium.webdriver.common.by import By
import google.generativeai as genai
import time
from PIL import Image
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os


def getCredentials():
    with open("user.txt", "r") as f:
        email = f.readline().strip()
        password = f.readline().strip()
        gemini_key = f.readline().strip()
    return email, password, gemini_key


def send_email(subject, body, sender, recipients, password, image_paths=[]):
    # Criação do objeto de mensagem
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)

    # Anexando o corpo do e-mail
    msg.attach(MIMEText(body, "plain"))

    # Anexando imagens
    for image_path in image_paths:
        # Verifica se o caminho da imagem é válido
        if os.path.isfile(image_path):
            with open(image_path, "rb") as image_file:
                # Criação do anexo
                part = MIMEBase("application", "octet-stream")
                part.set_payload(image_file.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(image_path)}",
                )
                msg.attach(part)
        else:
            print(f"Imagem não encontrada: {image_path}")

    # Enviando o e-mail
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, recipients, msg.as_string())


def main():
    email, password, gemini_key = getCredentials()

    driver = webdriver.Chrome()

    driver.set_window_size(1920, 1080)

    driver.get("https://investidor10.com.br/login")

    driver.find_element("name", "email").send_keys(email)

    driver.find_element("name", "password").send_keys(password)

    driver.find_element(By.XPATH, '//input[@value="Entrar"]').click()

    time.sleep(5)

    driver.execute_script("window.localStorage.setItem('wallet-tutorial','true');")

    driver.get("https://investidor10.com.br/carteiras/resumo")

    time.sleep(5)

    header_element = driver.find_element(By.CLASS_NAME, "site-header")

    header_element.screenshot("header.png")

    driver.execute_script(
        """
    var elements = document.getElementsByClassName('ticker-list');
    for (var i = 0; i < elements.length; i++) {
        elements[i].classList.add('active');
    }
"""
    )

    time.sleep(5)

    ticker_elements = driver.find_elements(By.CLASS_NAME, "ticker-list")

    for index, element in enumerate(ticker_elements):
        driver.execute_script("arguments[0].scrollIntoView();", element)
        time.sleep(1)
        element.screenshot(f"ticker_{index}.png")

    driver.quit()

    images = [Image.open(f"ticker_{i}.png") for i in range(5)]
    widths, heights = zip(*(i.size for i in images))
    total_width = max(widths)
    max_height = sum(heights)
    new_image = Image.new("RGB", (total_width, max_height))
    y_offset = 0

    for im in images:
        new_image.paste(im, (0, y_offset))
        y_offset += im.size[1]

    new_image.save("tickers.png")

    genai.configure(api_key=gemini_key)
    header_png = genai.upload_file("./header.png")
    tickers_png = genai.upload_file("./tickers.png")

    model = genai.GenerativeModel("gemini-1.5-flash")
    result = model.generate_content(
        [
            header_png,
            tickers_png,
            "\n\n",
            "Resuma as variações dessa carteira. A primeira imagem mostra o saldo total (valor que a carteira possui) e o valor aplicado (quanto foi aportado), comente sobre o valor aplicado e o saldo bruto. A segunda mostra os ativos que compõem a carteira sendo que o valor total é o valor aportado e o saldo é quanto cada conjunto de ativo está valendo, sendo que podem ter nenhum ou mais de um investimento por ativo. Os ativos que não tiverem nenhum investimento não precisam ser comentados. Não faça nenhuma conta para saber o saldo total, apenas use o que está nas imagens.",
        ]
    )

    subject = f"Resumo da carteira do dia {time.strftime('%d/%m/%Y')}"
    body = "Olá, segue o resumo da carteira de hoje:\n\n" + result.text
    sender = ""  # Seu endereço de e-mail do Gmail
    password = ""  # Sua senha de aplicativo
    recipients = [""]  # Endereço de e-mail do destinatário
    image_paths = [
        "./tickers.png",
        "./header.png",
    ]  # Caminhos das imagens a serem anexadas

    # Envio do e-mail
    send_email(subject, body, sender, recipients, password, image_paths)


main()
