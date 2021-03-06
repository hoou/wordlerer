import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from . import english_words
from .models import Feedback, SingleFeedback
from .wordlerer import Wordlerer


class BrowserApp:
    WORD_SIZE = 5
    KEYBOARD = {
        "Q": "div:nth-child(1) > button:nth-child(1)",
        "W": "div:nth-child(1) > button:nth-child(2)",
        "E": "div:nth-child(1) > button:nth-child(3)",
        "R": "div:nth-child(1) > button:nth-child(4)",
        "T": "div:nth-child(1) > button:nth-child(5)",
        "Y": "div:nth-child(1) > button:nth-child(6)",
        "U": "div:nth-child(1) > button:nth-child(7)",
        "I": "div:nth-child(1) > button:nth-child(8)",
        "O": "div:nth-child(1) > button:nth-child(9)",
        "P": "div:nth-child(1) > button:nth-child(10)",
        "A": "div:nth-child(2) > button:nth-child(2)",
        "S": "div:nth-child(2) > button:nth-child(3)",
        "D": "div:nth-child(2) > button:nth-child(4)",
        "F": "div:nth-child(2) > button:nth-child(5)",
        "G": "div:nth-child(2) > button:nth-child(6)",
        "H": "div:nth-child(2) > button:nth-child(7)",
        "J": "div:nth-child(2) > button:nth-child(8)",
        "K": "div:nth-child(2) > button:nth-child(9)",
        "L": "div:nth-child(2) > button:nth-child(10)",
        "Z": "div:nth-child(3) > button:nth-child(2)",
        "X": "div:nth-child(3) > button:nth-child(3)",
        "C": "div:nth-child(3) > button:nth-child(4)",
        "V": "div:nth-child(3) > button:nth-child(5)",
        "B": "div:nth-child(3) > button:nth-child(6)",
        "N": "div:nth-child(3) > button:nth-child(7)",
        "M": "div:nth-child(3) > button:nth-child(8)",
        "ENTER": "div:nth-child(3) > button:nth-child(1)",
        "BACKSPACE": "button.one-and-a-half:nth-child(9)",
    }

    def __init__(self, auto: bool = True):
        print("creating driver")
        self.driver = webdriver.Firefox()
        self.feedback_number = 0
        self.auto = auto

    def _get_game(self) -> WebElement:
        game_app = self._get_game_app()
        game_theme_manager = self._expand_shadow_element(game_app)[1]
        return game_theme_manager.find_element(By.ID, "game")

    def _get_keyboard(self) -> WebElement:
        game_keyboard = self._get_game().find_element(By.TAG_NAME, "game-keyboard")
        return self._expand_shadow_element(game_keyboard)[1]

    def _get_feedback(self, word: str) -> Feedback:
        print(f"getting feedback for word: {word}")

        keyboard = self._get_keyboard()
        game = self._get_game()

        for w in word:
            self._click_on_key(keyboard, key=w)
        self._confirm_word(keyboard)

        self._wait(3)

        single_feedbacks = []

        game_row = game.find_element(
            By.CSS_SELECTOR, f"#board > game-row:nth-child({self.feedback_number + 1})"
        )
        row = self._expand_shadow_element(game_row)[1]

        for i in range(self.WORD_SIZE):
            game_tile: WebElement = row.find_element(
                By.CSS_SELECTOR, f"game-tile:nth-child({i + 1})"
            )
            evaluation = game_tile.get_attribute("evaluation")
            if not evaluation:
                self._clean_row(keyboard)
                return Feedback(word_in_list=False)
            single_feedbacks.append(SingleFeedback(evaluation))

        self.feedback_number += 1

        print(single_feedbacks)

        return Feedback(single_feedbacks=single_feedbacks)

    def _click_on_key(self, keyboard: WebElement, key: str):
        print(f"clicking on key: {key}")
        key_element: WebElement = keyboard.find_element(
            By.CSS_SELECTOR, self.KEYBOARD[key.upper()]
        )
        key_element.click()

    def _expand_shadow_element(self, element: WebElement) -> list[WebElement]:
        return self.driver.execute_script(
            "return arguments[0].shadowRoot.children", element
        )

    def _close_modal(self):
        print("closing modal")
        game = self._get_game()
        game.click()
        print("modal closed")

    def _get_game_app(self):
        return self.driver.find_element(By.TAG_NAME, "game-app")

    def _confirm_word(self, keyboard_element: WebElement):
        print("confirming word")
        self._click_on_key(keyboard_element, "ENTER")

    @staticmethod
    def _wait(seconds: int):
        print(f"waiting {seconds} seconds")
        time.sleep(seconds)

    @staticmethod
    def _choose(options: list[str]) -> str:
        print(options)
        while True:
            word = input("choose one word: ")
            if word not in options:
                print("this was not an option")
            else:
                return word

    def _clean_row(self, keyboard: WebElement) -> None:
        print("wrong word, cleaning row")
        for _ in range(self.WORD_SIZE):
            self._click_on_key(keyboard, "BACKSPACE")

    def run(self):
        print("going on website")
        self.driver.get("https://www.powerlanguage.co.uk/wordle/")
        self.driver.maximize_window()
        self._close_modal()

        wordlerer = Wordlerer(
            words=english_words.lower_alpha_set,
            word_size=self.WORD_SIZE,
            feedback_handler=self._get_feedback,
            choice_handler=self._choose if not self.auto else None,
        )
        if wordlerer.solve():
            print("congrats!")
        else:
            print("you lost :(")
