#  Module Imports
import sys
import pygame
import random
import numpy as np

pygame.init()

class Ship:
    def __init__(self, name, img, pos, size, numGuns=0, gunPath=None, gunsize=None, gunCoordsOffset=None):
        self.name = name
        self.pos = pos
        self.size = size
        self.rotation = False  # False: Vertical, True: Horizontal
        self.active = False
        self.gunslist = []
        self._load_images(img)
        self._initialize_guns(numGuns, gunPath, gunsize, gunCoordsOffset)

    def _load_images(self, img):
        """Tải và chuẩn bị hình ảnh tàu theo hướng dọc và ngang."""
        self.vImage = loadImage(img, self.size)
        self.vImageRect = self.vImage.get_rect(topleft=self.pos)
        self.hImage = pygame.transform.rotate(self.vImage, -90)
        self.hImageRect = self.hImage.get_rect(topleft=self.pos)
        self.image, self.rect = self.vImage, self.vImageRect

    def _initialize_guns(self, numGuns, gunPath, gunsize, gunCoordsOffset):
        """Khởi tạo súng của tàu nếu có."""
        if numGuns > 0 and gunPath:
            for i in range(numGuns):
                gun_size = (self.size[0] * gunsize[0], self.size[1] * gunsize[1])
                self.gunslist.append(
                    Guns(gunPath, self.rect.center, gun_size, gunCoordsOffset[i])
                )

    def selectShipAndMove(self):
        """Kích hoạt chuyển động của tàu bằng chuột."""
        self.active = True
        while self.active:
            self.rect.center = pygame.mouse.get_pos() # Cập nhật vị trí tàu, khiến tàu di chuyển theo chuột
            updateGameScreen(GAMESCREEN, GAMESTATE, True)
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.checkForCollisions(pFleet):
                        if event.button == 1:  # Left click to place
                            self._finalize_placement()
                        elif event.button == 3:  # Right click to rotate
                            self.rotateShip()

    def _finalize_placement(self):
        """Hoàn tất việc đặt tàu."""
        self.hImageRect.center = self.vImageRect.center = self.rect.center
        self.active = False

    def rotateShip(self, force=False):
        """Chuyển đổi tàu giữa hướng dọc và hướng ngang."""
        #chuyển nếu 1 trong 2 điều kiện: khi tàu đang ở state active hoặc buộc phải xoay (do mong muốn của người thiết lập)
        if self.active or force:               
            self.rotation = not self.rotation   
            self._switch_image_and_rect()

    def _switch_image_and_rect(self):
        """Switch between vertical and horizontal images."""
        #True: Ngang, False:Dọc
        self.image, self.rect = (self.hImage, self.hImageRect) if self.rotation else (self.vImage, self.vImageRect)
        self.hImageRect.center = self.vImageRect.center = self.rect.center

    def checkForCollisions(self, shiplist):
        """Kiểm tra xem tàu ​​có va chạm với tàu nào khác trong hạm đội không."""
        return any(self.rect.colliderect(ship.rect) for ship in shiplist if ship != self)

    def returnToDefaultPosition(self):
        """Đặt lại tàu về vị trí và hướng mặc định."""
        if self.rotation:                   #Nếu tàu đang nằm ngang
            self.rotateShip(force=True)     #Quay tàu dọc với force là True
        self.rect.topleft = self.pos
        self.hImageRect.center = self.vImageRect.center = self.rect.center

    def snapToGridEdge(self, gridCoords):
        """Chuyển tàu vào cạnh lưới hoặc trở về mặc định nếu vượt quá giới hạn."""
        left, right, top, bottom = gridCoords[0][0][0], gridCoords[0][-1][0] + 50, gridCoords[0][0][1], gridCoords[-1][0][1] + 50
        if self.rect.left < left or self.rect.right > right or self.rect.top < top or self.rect.bottom > bottom:
            self.returnToDefaultPosition()
        else:
            self._constrain_within_bounds(left, right, top, bottom)
        self.vImageRect.center = self.hImageRect.center = self.rect.center

    def _constrain_within_bounds(self, left, right, top, bottom):
        """Hạn chế vị trí của tàu trong phạm vi lưới."""
        self.rect.left = max(self.rect.left, left)
        self.rect.right = min(self.rect.right, right)
        self.rect.top = max(self.rect.top, top)
        self.rect.bottom = min(self.rect.bottom, bottom)

    def snapToGrid(self, gridCoords):
        """Cập nhật vị trí tàu vào ô lưới gần nhất."""
        for row in gridCoords:
            for cell in row:
                if self.rect.left >= cell[0] and self.rect.left < cell[0] + CELLSIZE and \
                   self.rect.top >= cell[1] and self.rect.top < cell[1] + CELLSIZE:
                    offset_x = (CELLSIZE - self.image.get_width()) // 2 if not self.rotation else 0
                    offset_y = 0 if not self.rotation else (CELLSIZE - self.image.get_height()) // 2
                    self.rect.topleft = (cell[0] + offset_x, cell[1] + offset_y)
        self.vImageRect.center = self.hImageRect.center = self.rect.center

    def draw(self, window):
        """Draw the ship and its guns on the window."""
        window.blit(self.image, self.rect)
        for gun in self.gunslist:
            gun.draw(window, self)


class Guns:
    def __init__(self, imgPath, pos, size, offset):
        self.orig_image = loadImage(imgPath, size, True)
        self.image = self.orig_image
        self.offset = offset
        self.rect = self.image.get_rect(center=pos)

    def update(self, ship):
        """Cập nhật vị trí và góc quay của súng dựa trên con tàu."""
        self._update_position(ship)
        self._rotate_gun(ship)

    def _update_position(self, ship):
        """Cập nhật vị trí của súng dựa trên hướng và độ lệch của tàu."""
        if not ship.rotation:  # Vertical orientation
            self.rect.center = (
                ship.rect.centerx,
                ship.rect.centery + (ship.image.get_height() // 2 * self.offset)
            )
        else:  # Horizontal orientation
            self.rect.center = (
                ship.rect.centerx + (ship.image.get_width() // 2 * -self.offset),
                ship.rect.centery
            )

    def _rotate_gun(self, ship):
        """Xoay súng theo con trỏ chuột dựa trên hướng tàu."""
        direction = pygame.math.Vector2(pygame.mouse.get_pos()) - pygame.math.Vector2(self.rect.center)
        _, angle = direction.as_polar()
        if self._is_valid_rotation(ship, angle):
            self._update_image(angle)

    def _is_valid_rotation(self, ship, angle):
        """Kiểm tra xem việc xoay súng có hợp lệ hay không dựa trên hướng và vị trí của tàu."""
        if not ship.rotation:  # Vertical orientation
            return (self.rect.centery <= ship.vImageRect.centery and angle <= 0) or \
                   (self.rect.centery >= ship.vImageRect.centery and angle > 0)
        else:  # Horizontal orientation
            return (self.rect.centerx <= ship.hImageRect.centerx and (angle <= -90 or angle >= 90)) or \
                   (self.rect.centerx >= ship.hImageRect.centerx and -90 <= angle <= 90)

    def _update_image(self, angle):
        """Cập nhật hình ảnh súng dựa trên góc quay."""
        self.image = pygame.transform.rotate(self.orig_image, -angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def draw(self, window, ship):   
        """Vẽ súng lên màn hình."""
        self.update(ship)
        window.blit(self.image, self.rect)


class Button:
    def __init__(self, image, size, pos, msg):
        self.name = msg
        self.image = image
        self.imageLarger = pygame.transform.scale(image, (size[0] + 10, size[1] + 10))
        self.rect = self.image.get_rect(topleft=pos)
        self.active = False
        self.radarUsed = 0

        # Create message text
        self.msg = self._create_text(msg)
        self.msgRect = self.msg.get_rect(center=self.rect.center)

    def _create_text(self, msg): 
        """Tạo văn bản hiển thị cho nút."""
        font = pygame.font.SysFont('Stencil', 22)
        return font.render(msg, True, (255, 255, 255))

    def focus_on_button(self, window):
        """Highlights nút khi được di chuột"""
        if self.active and self.rect.collidepoint(pygame.mouse.get_pos()):
            window.blit(self.imageLarger, (self.rect.x - 5, self.rect.y - 5))
        else:
            window.blit(self.image, self.rect)

    def handle_action(self):
        """Thực hiện hành động tương ứng dựa trên tên của nút."""
        if not self.active:
            return

        actions = {
            'Randomize': lambda: (self._randomize_positions(pFleet, pGameGrid),
                                  self._randomize_positions(cFleet, cGameGrid)),
            'SparseFix': lambda: (self._fixed_positions_ofShip(pFleet, pGameGrid)),
            'SeamlessFix': lambda: (self._sfixed_positions_ofShip(pFleet, pGameGrid)),
            'Reset': lambda: self._reset_ships(pFleet),
            'Start': self._deployment_phase,
            'Quit': lambda: None,  # Define a quit logic here if needed
            'Redeploy': self._restart_game
        }

        action = actions.get(self.name)
        if action:
            action()


    def _sfixed_positions_ofShip(self, shiplist, gameGrid):
        if DEPLOYMENT:
            placeShipsAtSeamlessFixedPositions(shiplist, gameGrid)

    def _fixed_positions_ofShip(self, shiplist, gameGrid):
        if DEPLOYMENT:
            placeShipsAtFixedPositions(shiplist, gameGrid)

    def _randomize_positions(self, shiplist, gameGrid):
        """Đặt ngẫu nhiên vị trí tàu."""
        if DEPLOYMENT:
            randomizeShipPositions(shiplist, gameGrid)

    def _reset_ships(self, shiplist):
        """Đặt lại tất cả các tàu về vị trí mặc định của chúng."""
        if DEPLOYMENT:
            for ship in shiplist:
                ship.returnToDefaultPosition()

    def _deployment_phase(self):
        """Giữ chỗ cho logic giai đoạn DEPLOYMENT."""
        pass

    def _restart_game(self):
        """Đặt lại trạng thái trò chơi."""
        TOKENS.clear()
        self._reset_ships(pFleet)
        self._randomize_positions(cFleet, cGameGrid)
        updateGameLogic(cGameGrid, cFleet, cGameLogic)
        updateGameLogic(pGameGrid, pFleet, pGameLogic)

    def _update_button_name(self, gameStatus):
        """Cập nhật tên nút động dựa trên trạng thái trò chơi."""
        name_map = {
            'Start': 'Redeploy' if not gameStatus else 'Start',
            'Redeploy': 'Start' if gameStatus else 'Redeploy',
            'Reset': 'Radar Scan' if not gameStatus else 'Reset',
            'Radar Scan': 'Reset' if gameStatus else 'Radar Scan',
            'Randomize': 'Quit' if not gameStatus else 'Randomize',
            'Quit': 'Randomize' if gameStatus else 'Quit',
        }
        self.name = name_map.get(self.name, self.name)
        self.msg = self._create_text(self.name)
        self.msgRect = self.msg.get_rect(center=self.rect.center)

    def draw(self, window):
        """Draws the button on the screen."""
        self._update_button_name(DEPLOYMENT)
        self.focus_on_button(window)
        window.blit(self.msg, self.msgRect)

class Tokens:
    def __init__(self, image, pos, action, imageList=None, explosionList=None, soundFile=None):
        self.image = image
        self.rect = self.image.get_rect()
        self.pos = pos
        self.rect.topleft = self.pos
        self.imageList = imageList
        self.explosionList = explosionList
        self.action = action
        self.soundFile = soundFile
        self.timer = pygame.time.get_ticks()
        self.imageIndex = 0
        self.explosionIndex = 0
        self.explosion = False

    def animate_Explosion(self):
        """Hiệu ứng chuỗi vụ nổ"""
        self.explosionIndex += 1
        if self.explosionIndex < len(self.explosionList):
            return self.explosionList[self.explosionIndex]
        else:
            return self.animate_fire()

    def animate_fire(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.timer >= 100:
            self.timer = current_time
            self.imageIndex += 1
        if self.imageIndex < len(self.imageList):
            return self.imageList[self.imageIndex]
        else:
            self.imageIndex = 0
            return self.imageList[self.imageIndex]

    def draw(self, window):
        """Vẽ token ra màn hình"""
        if not self.imageList:  # Nếu không có imageList nào được cung cấp, hãy sử dụng một hình ảnh
            window.blit(self.image, self.rect)
        else:
            self.image = self.animate_Explosion()  # Sử dụng animate_Explosion() nếu imageList được cung cấp
            self.rect = self.image.get_rect(topleft=self.pos)
            self.rect[1] = self.pos[1] - 10  # Điều chỉnh vị trí y một chút để căn chỉnh tốt hơn
            window.blit(self.image, self.rect)

class Player:
    def __init__(self):
        self.turn = True

    def make_attack(self, grid, logic_grid):
        """Xử lý cuộc tấn công của người chơi vào lưới máy tính dựa trên vị trí chuột."""
        posX, posY = pygame.mouse.get_pos()

        # Kiểm tra xem vị trí chuột có nằm trong giới hạn lưới không
        if self._is_within_bounds(posX, posY, grid):
            for i, row in enumerate(grid):
                for j, col in enumerate(row):
                    if self._is_cell_clicked(posX, posY, col):
                        self._process_attack(i, j, grid, logic_grid)

    def _is_within_bounds(self, posX, posY, grid):
        # Kiểm tra xem vị trí chuột có nằm trong giới hạn lưới không
        return (grid[0][0][0] <= posX <= grid[0][-1][0] + 50 and
                grid[0][0][1] <= posY <= grid[-1][0][1] + 50)

    def _is_cell_clicked(self, posX, posY, cell):
        """Kiểm tra xem một ô lưới cụ thể có được nhấp vào hay không."""
        return cell[0] <= posX < cell[0] + 50 and cell[1] <= posY < cell[1] + 50

    def _process_attack(self, i, j, grid, logic_grid):
        """Xử lý kết quả đòn tấn công của người chơi."""
        # Kiểm tra nếu ô đã được đánh dấu trước đó
        if logic_grid[i][j] in ('X', 'T'):
            return

        if logic_grid[i][j] != ' ':
            if logic_grid[i][j] == 'O':  # Hit
                TOKENS.append(Tokens(REDTOKEN, grid[i][j], 'Hit', None, None, None))
                logic_grid[i][j] = 'T'
                SHOTSOUND.play()
                HITSOUND.play()
            self.turn = False  # End player's turn
        else:  # Miss
            logic_grid[i][j] = 'X'
            TOKENS.append(Tokens(GREENTOKEN, grid[i][j], 'Miss', None, None, None))
            SHOTSOUND.play()
            MISSSOUND.play()
            self.turn = False  # End player's turn

#Các thuật toán của computer
#Tìm kiếm mù: DFS
class DFSCOMPUTER:
    def __init__(self):
        # Biến điều khiển lượt chơi của máy
        self.turn = False  # Biến cho biết máy đang ở lượt chơi hay không
        self.status = self.computer_status('Thinking')  # Trạng thái hiện tại của máy
        self.name = 'DFS Computer'  # Tên của máy
        self.visited = set()  # Tập hợp các ô đã bắn (tránh lặp lại)
        self.stack = []  # Ngăn xếp để thực hiện thuật toán tìm kiếm theo chiều sâu (DFS)

    def computer_status(self, msg):
        """Hiển thị trạng thái của máy."""
        font = pygame.font.SysFont('Stencil', 22)
        return font.render(msg, 1, (0, 0, 0))

    def make_attack(self, gamelogic):
        """
        Máy thực hiện lượt tấn công:
        - Nếu ngăn xếp rỗng, khởi tạo tất cả ô trên lưới vào ngăn xếp.
        - Lấy các ô từ ngăn xếp để thực hiện bắn theo DFS.
        """
        current_time = pygame.time.get_ticks()  # Lấy thời gian hiện tại
        if current_time - TURNTIMER >= 1000:  # Kiểm tra nếu đã qua ít nhất 1 giây từ lượt trước
            if not self.stack:  # Nếu ngăn xếp rỗng
                for row in range(10):  # Duyệt qua toàn bộ lưới
                    for col in range(10):
                        self.stack.append((row, col))  # Thêm tất cả ô vào ngăn xếp
            # Lấy các ô tiếp theo từ ngăn xếp
            while self.stack:
                row, col = self.stack.pop()  # Lấy ô cuối cùng trong ngăn xếp
                if (row, col) not in self.visited:  # Chỉ xử lý ô chưa bị bắn
                    self._process_attack(row, col, gamelogic)  # Cập nhật trạng thái của ô vừa tấn công
                    break
        return self.turn  # Trả về trạng thái lượt chơi của máy

    def _process_attack(self, row, col, gamelogic):
        """
        Thực hiện bắn vào ô (row, col) và cập nhật trạng thái:
        - Nếu bắn trúng tàu, cập nhật ô trúng và thêm các ô lân cận vào ngăn xếp.
        - Nếu bắn trượt, cập nhật ô trượt.
        """
        print(f"Attacking: ({row}, {col})")  # In ra vị trí đang bắn
        self.visited.add((row, col))  # Đánh dấu ô đã bắn
        if gamelogic[row][col] == 'O':  # Nếu ô chứa tàu
            gamelogic[row][col] = 'T'  # Đánh dấu trạng thái ô trúng tàu
            # Thêm hiệu ứng và âm thanh khi bắn trúng
            TOKENS.append(Tokens(REDTOKEN, pGameGrid[row][col], 'Hit', FIRETOKENIMAGELIST, EXPLOSIONIMAGELIST, None))
            SHOTSOUND.play()
            HITSOUND.play()
            # Thêm các ô lân cận vào ngăn xếp để tiếp tục DFS
            self._add_neighbors_to_stack(row, col, gamelogic)
        else:  # Nếu bắn trượt
            gamelogic[row][col] = 'X'  # Đánh dấu trạng thái ô trượt
            # Thêm hiệu ứng và âm thanh khi bắn trượt
            TOKENS.append(Tokens(BLUETOKEN, pGameGrid[row][col], 'Miss', None, None, None))
            SHOTSOUND.play()
            MISSSOUND.play()
        # Kết thúc lượt chơi
        self.turn = False

    def _add_neighbors_to_stack(self, row, col, gamelogic):
        """
        Thêm các ô lân cận (theo 4 hướng: Bắc, Nam, Đông, Tây) vào ngăn xếp để tiếp tục DFS.
        """
        directions = ['North', 'South', 'East', 'West']  # Các hướng di chuyển
        for direction in directions:
            # Lấy tọa độ ô lân cận dựa trên hướng
            nx, ny = self._get_next_position(row, col, direction)
            # Chỉ thêm ô hợp lệ (nằm trong lưới, chưa bị bắn)
            if self.is_within_grid(nx, ny) and (nx, ny) not in self.visited:
                if gamelogic[nx][ny] in ['O', ' ']:  # Ô khả nghi (chứa tàu hoặc chưa khám phá)
                    self.stack.append((nx, ny))  # Thêm ô vào ngăn xếp

    def _get_next_position(self, x, y, direction):
        """
        Trả về vị trí tiếp theo dựa trên hướng:
        - 'North': Lên
        - 'South': Xuống
        - 'East': Sang phải
        - 'West': Sang trái
        """
        if direction == 'North':
            return x - 1, y
        elif direction == 'South':
            return x + 1, y
        elif direction == 'East':
            return x, y + 1
        elif direction == 'West':
            return x, y - 1
        return x, y  # Trả về vị trí ban đầu nếu hướng không hợp lệ

    def is_within_grid(self, x, y):
        # Kiểm tra xem tọa độ (x, y) có nằm trong lưới (10x10) hay không.
        return 0 <= x < 10 and 0 <= y < 10

    def draw(self, window):
        """
        Hiển thị trạng thái của máy lên màn hình:
        - Nếu đang ở lượt chơi, hiển thị trạng thái 'Thinking'.
        """
        if self.turn:
            window.blit(self.status, (cGameGrid[0][0][0] - CELLSIZE, cGameGrid[-1][-1][1] + CELLSIZE))


# Quay lui (Backtracking)
class BTCOMPUTER:
    def __init__(self):
        # Khởi tạo trạng thái ban đầu của máy tính
        self.turn = False  # Biến xác định liệu có phải lượt của máy hay không
        self.status = self.computer_status('Thinking')  # Trạng thái hiển thị của máy
        self.name = 'Backtracking Computer'  # Tên của máy
        self.moves = []  # Danh sách các ô cần tấn công theo chiến thuật backtracking
        self.visited = set()  # Tập hợp các ô đã được bắn

    def computer_status(self, msg):
        """Hiển thị trạng thái của máy."""
        font = pygame.font.SysFont('Stencil', 22)
        return font.render(msg, 1, (0, 0, 0))

    def make_attack(self, gamelogic):
        """
        Máy thực hiện lượt tấn công:
        - Nếu danh sách `self.moves` trống, máy chọn ngẫu nhiên một ô chưa được bắn.
        - Nếu `self.moves` có ô, thực hiện tấn công theo chiến thuật backtracking.
        """
        current_time = pygame.time.get_ticks()  # Lấy thời gian hiện tại
        if len(self.moves) == 0 and current_time - TURNTIMER >= 1000:
            # Khi danh sách moves trống, chọn ngẫu nhiên một ô hợp lệ để bắn
            valid_choice = False
            while not valid_choice:
                row, col = random.randint(0, 9), random.randint(0, 9)  # Chọn tọa độ ngẫu nhiên
                # Kiểm tra ô chưa bắn và có khả năng chứa tàu
                if (row, col) not in self.visited and gamelogic[row][col] in [' ', 'O']:
                    valid_choice = True
            self._process_attack(row, col, gamelogic)  # Cập nhật trạng thái của ô vừa tấn công
        elif len(self.moves) > 0 and current_time - TURNTIMER >= 1000:
            # Khi danh sách moves có ô, thực hiện tấn công backtracking
            row, col = self.moves.pop()  # Lấy ô cuối cùng trong danh sách để bắn
            self._process_attack(row, col, gamelogic)
        return self.turn  # Trả về trạng thái lượt chơi của máy

    def _process_attack(self, row, col, gamelogic):
        """
        Thực hiện bắn vào ô (row, col) và cập nhật trạng thái:
        - Nếu bắn trúng tàu, thêm các ô lân cận vào danh sách moves.
        - Nếu bắn trượt, chỉ cập nhật trạng thái ô đó.
        """
        print(f"Attacking: ({row}, {col})")  # Debug vị trí bắn
        self.visited.add((row, col))  # Đánh dấu ô đã bắn
        if gamelogic[row][col] == 'O':  # Nếu ô chứa tàu
            gamelogic[row][col] = 'T'  # Đánh dấu trạng thái ô trúng tàu
            # Thêm hiệu ứng và âm thanh khi bắn trúng
            TOKENS.append(Tokens(REDTOKEN, pGameGrid[row][col], 'Hit', FIRETOKENIMAGELIST, EXPLOSIONIMAGELIST, None))
            SHOTSOUND.play()
            HITSOUND.play()
            # Gọi hàm thêm các ô lân cận vào danh sách backtracking
            self._backtrack_ship(row, col, gamelogic)
        else:  # Nếu bắn trượt
            gamelogic[row][col] = 'X'  # Đánh dấu trạng thái ô trượt
            # Thêm hiệu ứng và âm thanh khi bắn trượt
            TOKENS.append(Tokens(BLUETOKEN, pGameGrid[row][col], 'Miss', None, None, None))
            SHOTSOUND.play()
            MISSSOUND.play()
        # Kết thúc lượt chơi
        self.turn = False

    def _backtrack_ship(self, row, col, gamelogic):
        """
        Thêm các ô lân cận (theo 4 hướng: Bắc, Nam, Đông, Tây) vào danh sách moves
        để thực hiện chiến thuật backtracking khi bắn trúng tàu.
        """
        directions = ['North', 'South', 'East', 'West']  # Các hướng để tìm ô lân cận
        for direction in directions:
            nx, ny = self._get_next_position(row, col, direction)  # Lấy tọa độ ô lân cận
            # Kiểm tra ô hợp lệ và chưa được bắn
            if self.is_within_grid(nx, ny) and (nx, ny) not in self.visited:
                if gamelogic[nx][ny] in ['O', ' ']:  # Ô khả nghi (chứa tàu hoặc chưa khám phá)
                    self.moves.append((nx, ny))  # Thêm ô vào danh sách moves

    def _get_next_position(self, x, y, direction):
        """
        Trả về tọa độ của ô lân cận dựa trên hướng:
        - 'North': Lên
        - 'South': Xuống
        - 'East': Sang phải
        - 'West': Sang trái
        """
        if direction == 'North':
            return x - 1, y
        elif direction == 'South':
            return x + 1, y
        elif direction == 'East':
            return x, y + 1
        elif direction == 'West':
            return x, y - 1
        return x, y  # Trường hợp không hợp lệ

    def is_within_grid(self, x, y):
        """Kiểm tra xem tọa độ (x, y) có nằm trong lưới (10x10) hay không."""
        return 0 <= x < 10 and 0 <= y < 10

    def draw(self, window):
        """
        Hiển thị trạng thái của máy lên màn hình:
        - Nếu máy đang trong lượt chơi, hiển thị trạng thái 'Thinking'.
        """
        if self.turn:
            window.blit(self.status, (cGameGrid[0][0][0] - CELLSIZE, cGameGrid[-1][-1][1] + CELLSIZE))

# Tìm kiếm đối kháng
class ADVCOMPUTER():
    def __init__(self):
        # Khởi tạo đối tượng máy tính:
        self.turn = False
        self.status = self.computer_status('Thinking')
        self.name = 'Minimax Computer'
        self.visited = set()  # Tập các ô đã tấn công

    def computer_status(self, msg):
        """Render trạng thái của máy tính."""
        font = pygame.font.SysFont('Stencil', 22)
        return font.render(msg, 1, (0, 0, 0))

    def make_attack(self, gamelogic):
        """
        Máy tính thực hiện tấn công dựa trên thuật toán Minimax:
        - Duyệt qua tất cả các ô hợp lệ để giả lập nước đi.
        - Tính điểm của từng nước đi bằng cách gọi hàm Minimax.
        - Chọn nước đi có điểm cao nhất.
        """
        best_score = float('-inf')  # Điểm số tốt nhất ban đầu
        best_move = None  # Lưu trữ tọa độ nước đi tốt nhất

        # Duyệt qua toàn bộ lưới để tìm nước đi tốt nhất
        for row in range(10):
            for col in range(10):
                if (row, col) not in self.visited and gamelogic[row][col] in [' ', 'O']:
                    # Giả lập tấn công ô này
                    original = gamelogic[row][col]
                    gamelogic[row][col] = 'T' if original == 'O' else 'X'

                    # Tính điểm của nước đi với Minimax
                    score = self.minimax(gamelogic, 3, False, float('-inf'), float('inf'))

                    # Hoàn tác thay đổi trên lưới
                    gamelogic[row][col] = original

                    # Cập nhật nước đi tốt nhất nếu điểm số cao hơn
                    if score > best_score:
                        best_score = score
                        best_move = (row, col)

        # Thực hiện nước đi tốt nhất
        if best_move:
            self._process_attack(best_move[0], best_move[1], gamelogic)

        return self.turn

    def minimax(self, gamelogic, depth, is_maximizing, alpha, beta):
        """
        Thuật toán Minimax với Alpha-Beta Pruning:
        - Đệ quy duyệt qua các trạng thái của trò chơi.
        - Tối đa hóa điểm số cho máy tính hoặc tối thiểu hóa điểm số cho đối thủ.
        - Sử dụng Alpha-Beta để cắt bỏ các nhánh không cần thiết.
        """
        # Điều kiện dừng: độ sâu bằng 0 hoặc trò chơi kết thúc
        if depth == 0 or self.is_game_over(gamelogic):
            return self.evaluate(gamelogic)

        if is_maximizing:
            max_eval = float('-inf')  # Giá trị tốt nhất cho máy tính
            for row in range(10):
                for col in range(10):
                    if (row, col) not in self.visited and gamelogic[row][col] in [' ', 'O']:
                        # Giả lập nước đi
                        original = gamelogic[row][col]
                        gamelogic[row][col] = 'T' if original == 'O' else 'X'

                        # Gọi đệ quy Minimax cho đối thủ
                        eval = self.minimax(gamelogic, depth - 1, False, alpha, beta)

                        # Hoàn tác nước đi
                        gamelogic[row][col] = original

                        # Cập nhật giá trị tốt nhất và Alpha
                        max_eval = max(max_eval, eval)
                        alpha = max(alpha, eval)

                        # Cắt tỉa nếu Beta <= Alpha
                        if beta <= alpha:
                            break
            return max_eval
        else:
            # Giả lập đối thủ
            min_eval = float('inf')  # Giá trị tốt nhất cho đối thủ
            for row in range(10):
                for col in range(10):
                    if (row, col) not in self.visited and gamelogic[row][col] in [' ', 'O']:
                        # Giả lập nước đi
                        original = gamelogic[row][col]
                        gamelogic[row][col] = 'T' if original == 'O' else 'X'

                        # Gọi đệ quy Minimax cho máy tính
                        eval = self.minimax(gamelogic, depth - 1, True, alpha, beta)

                        # Hoàn tác nước đi
                        gamelogic[row][col] = original

                        # Cập nhật giá trị tốt nhất và Beta
                        min_eval = min(min_eval, eval)
                        beta = min(beta, eval)

                        # Cắt tỉa nếu Beta <= Alpha
                        if beta <= alpha:
                            break
            return min_eval

    def evaluate(self, gamelogic):
        """
        Hàm đánh giá trạng thái lưới:
        - Tính điểm dựa trên số ô đã bắn trúng tàu hoặc bắn trượt.
        - +10 điểm cho mỗi ô bắn trúng.
        - -5 điểm cho mỗi ô bắn trượt.
        """
        score = 0
        for row in range(10):
            for col in range(10):
                if gamelogic[row][col] == 'T':  # Đánh trúng tàu
                    score += 10
                elif gamelogic[row][col] == 'X':  # Trượt
                    score -= 5
        return score

    def is_game_over(self, gamelogic):
        """
        Kiểm tra xem trò chơi đã kết thúc hay chưa:
        - Nếu còn ô 'O' (tàu chưa bị bắn trúng), trò chơi chưa kết thúc.
        """
        for row in gamelogic:
            if 'O' in row:
                return False
        return True

    def _process_attack(self, row, col, gamelogic):
        """
        Xử lý kết quả của nước đi:
        - Cập nhật trạng thái lưới (đánh trúng hoặc trượt).
        - Thêm hiệu ứng hình ảnh/sound.
        """
        self.visited.add((row, col))
        print(f"Attacking: ({row}, {col})")
        if gamelogic[row][col] == 'O':
            gamelogic[row][col] = 'T'  # Đánh trúng tàu
            SHOTSOUND.play()
            HITSOUND.play()
            TOKENS.append(Tokens(REDTOKEN, pGameGrid[row][col], 'Hit', FIRETOKENIMAGELIST, EXPLOSIONIMAGELIST, None))
            print("Hit!")
        else:
            gamelogic[row][col] = 'X'  # Trượt
            TOKENS.append(Tokens(BLUETOKEN, pGameGrid[row][col], 'Miss', None, None, None))
            SHOTSOUND.play()
            MISSSOUND.play()
            print("Miss!")
        self.turn = False  # Kết thúc lượt

    def draw(self, window):
        """Hiển thị trạng thái của máy tính lên màn hình."""
        if self.turn:
            window.blit(self.status, (cGameGrid[0][0][0] - CELLSIZE, cGameGrid[-1][-1][1] + CELLSIZE))


class GCOMPUTER():
    def __init__(self):
        # Khởi tạo trạng thái của máy tính
        self.turn = False
        self.status = self.computer_status('Thinking')
        self.name = 'Greedy Computer'

        # Ma trận xác suất để máy tính quyết định vị trí tấn công, ban đầu phân bổ đều
        self.probability_matrix = np.full((10, 10), 1 / 100)

    def computer_status(self, msg):
        """Render trạng thái của máy tính."""
        font = pygame.font.SysFont('Stencil', 22)
        return font.render(msg, 1, (0, 0, 0))

    def update_probability(self, x, y, gamelogic, hit):
        """Cập nhật ma trận xác suất sau khi bắn."""
        n = self.probability_matrix.shape[0]  # Kích thước ma trận
        reduction_factor = 0.2  # Hệ số giảm xác suất ở các ô lân cận

        # Đặt xác suất của ô vừa bắn về 0 vì không còn khả năng chứa tàu
        self.probability_matrix[x, y] = 0

        if hit:  # Nếu bắn trúng tàu
            # Tăng xác suất các ô lân cận vì khả năng có phần còn lại của tàu
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < n and 0 <= ny < n and gamelogic[nx][ny] not in ['X', 'T']:
                    self.probability_matrix[nx, ny] += 0.3
        else:  # Nếu trượt
            # Giảm xác suất các ô lân cận vì khả năng không có tàu ở đây
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < n and 0 <= ny < n and gamelogic[nx][ny] not in ['X', 'T']:
                    self.probability_matrix[nx, ny] *= (1 - reduction_factor)

        # Chuẩn hóa lại ma trận xác suất để tổng xác suất = 1
        total_probability = np.sum(self.probability_matrix)
        if total_probability > 0:
            self.probability_matrix /= total_probability

    def choose_next_move(self):
        """Chọn vị trí bắn tiếp theo dựa trên xác suất cao nhất."""
        max_prob = np.max(self.probability_matrix)  # Lấy xác suất lớn nhất trong ma trận
        # Lấy tất cả các ô có xác suất lớn nhất
        candidates = np.argwhere(self.probability_matrix == max_prob)
        # Chọn ngẫu nhiên một ô trong danh sách các ô có xác suất cao nhất
        chosen = random.choice(candidates)
        return tuple(chosen)

    def make_attack(self, gamelogic):
        """Thực hiện bước tấn công."""
        current_time = pygame.time.get_ticks()  # Lấy thời gian hiện tại

        # Nếu đã qua thời gian cần thiết, chọn ô tiếp theo để tấn công
        if current_time - TURNTIMER >= 1000:
            row, col = self.choose_next_move()  # Chọn ô dựa trên xác suất cao nhất
            self._process_attack(row, col, gamelogic)  # Xử lý kết quả tấn công

        return self.turn

    def _process_attack(self, row, col, gamelogic):
        """Xử lý kết quả của bước tấn công."""
        print(f"Attacking: ({row}, {col})")  # In vị trí tấn công
        if gamelogic[row][col] == 'O':  # Nếu đánh trúng tàu
            gamelogic[row][col] = 'T'  # Đánh dấu ô đó là trúng
            self.update_probability(row, col, gamelogic, hit=True)  # Cập nhật xác suất
            # Thêm token trúng tàu và phát âm thanh
            TOKENS.append(Tokens(REDTOKEN, pGameGrid[row][col], 'Hit', FIRETOKENIMAGELIST, EXPLOSIONIMAGELIST, None))
            SHOTSOUND.play()
            HITSOUND.play()
        else:  # Nếu đánh trượt
            gamelogic[row][col] = 'X'  # Đánh dấu ô đó là trượt
            self.update_probability(row, col, gamelogic, hit=False)  # Cập nhật xác suất
            # Thêm token trượt và phát âm thanh
            TOKENS.append(Tokens(BLUETOKEN, pGameGrid[row][col], 'Miss', None, None, None))
            SHOTSOUND.play()
            MISSSOUND.play()

        self.turn = False  # Kết thúc lượt của máy

    def draw(self, window):
        """Vẽ trạng thái của máy trên cửa sổ."""
        if self.turn:
            window.blit(self.status, (cGameGrid[0][0][0] - CELLSIZE, cGameGrid[-1][-1][1] + CELLSIZE))


class OPTIMALMODE:
    def __init__(self):
        self.turn = False  # Biến xác định lượt đi của máy tính.
        self.status = self.computer_status('Thinking')  # Hiển thị trạng thái hiện tại của máy tính.
        self.name = 'Optimal Computer'  # Tên chế độ.
        self.probability_matrix = np.full((10, 10), 1 / 100)  # Ma trận xác suất khởi tạo, tất cả ô có xác suất 1/100.
        self.moves = []  # Danh sách các nước đi ưu tiên sau khi bắn trúng.

    def computer_status(self, msg):
        """Render trạng thái cho máy tính."""
        font = pygame.font.SysFont('Stencil', 22)
        return font.render(msg, 1, (0, 0, 0))

    def update_probability(self, x, y, gamelogic):
        """Cập nhật ma trận xác suất sau khi bắn hụt."""
        reduction_factor = 0.2  # Tỷ lệ giảm xác suất ở các ô lân cận
        n = self.probability_matrix.shape[0]

        # Đặt xác suất của ô đã bắn về 0
        self.probability_matrix[x, y] = 0

        # Giảm xác suất ở các ô lân cận chưa bị bắn
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (-1, -1), (1, -1), (-1, 1)]:  # Chỉ các ô lân cận
            nx, ny = x + dx, y + dy
            if 0 <= nx < n and 0 <= ny < n and gamelogic[nx][ny] not in ['X', 'T']: # Nếu ô chưa bị bắn.
                self.probability_matrix[nx, ny] *= (1 - reduction_factor)   # Giảm xác suất của ô.

        # Chuẩn hóa lại ma trận để tổng xác suất vẫn bằng 1
        total_probability = np.sum(self.probability_matrix)
        if total_probability > 0:
            self.probability_matrix /= total_probability

        print(f"Ma trận xác suất sau khi bắn vào ({x}, {y}):")
        self.print_probability_matrix()

    def choose_next_move(self):
        """Chọn vị trí bắn tiếp theo dựa trên ma trận xác suất."""
        n = self.probability_matrix.shape[0]  # Kích thước ma trận.
        flat_probs = self.probability_matrix.flatten()  # Chuyển ma trận thành mảng 1D.
        index = np.random.choice(range(n * n), p=flat_probs)  # Chọn ngẫu nhiên một ô dựa trên phân phối xác suất.
        row, col = divmod(index, n)  # Chuyển chỉ số 1D thành tọa độ 2D.
        return row, col  # Trả về tọa độ của ô được chọn.

    def make_attack(self, gamelogic):
        """Thực hiện tấn công dựa trên lượt và trạng thái."""
        current_time = pygame.time.get_ticks()  # Lấy thời gian hiện tại

        # Nếu không có nước đi ưu tiên và đủ thời gian
        if len(self.moves) == 0 and current_time - TURNTIMER >= 1000:
            row, col = self.choose_next_move()  # Chọn ô bắn
            self._process_attack(row, col, gamelogic)  # Thực hiện tấn công

        # Nếu có nước đi ưu tiên
        elif len(self.moves) > 0 and current_time - TURNTIMER >= 1000:
            row, col = self.moves[0]  # Lấy nước đi ưu tiên đầu tiên
            self._process_attack(row, col, gamelogic)  # Thực hiện tấn công
            self.moves.pop(0)  # Xóa nước đi đã xử lý khỏi danh sách

        return self.turn  # Trả về trạng thái lượt

    def _process_attack(self, row, col, gamelogic):
        print(f"Attacking: ({row}, {col})")
        if gamelogic[row][col] == 'O':  # Hit
            TOKENS.append(Tokens(REDTOKEN, pGameGrid[row][col], 'Hit', FIRETOKENIMAGELIST, EXPLOSIONIMAGELIST, None))
            gamelogic[row][col] = 'T'

            self.probability_matrix[row, col] = 0 # Xác suất của ô đã bắn được đặt về 0.
            total_probability = np.sum(self.probability_matrix)
            if total_probability > 0:
                self.probability_matrix /= total_probability # Chuẩn hóa ma trận để tổng xác suất = 1.

            SHOTSOUND.play()
            HITSOUND.play()
            if any(gamelogic[nx][ny] == 'T' for nx, ny in self.moves):
                self.generate_moves2((row, col), gamelogic) # Sinh các nước đi ưu tiên dựa trên trục hiện tại của tàu.
            else:
                self.generate_moves((row, col), gamelogic) # Sinh các nước đi ưu tiên.
        else:  # Miss
            gamelogic[row][col] = 'X'
            self.update_probability(row, col, gamelogic)
            TOKENS.append(Tokens(BLUETOKEN, pGameGrid[row][col], 'Miss', None, None, None))
            SHOTSOUND.play()
            MISSSOUND.play()

        self.turn = False  # End computer's turn

    def is_within_grid(self, x, y):
        return 0 <= x < 10 and 0 <= y < 10

    def generate_moves2(self, coords, grid):
        """Sinh các nước đi ưu tiên sau khi bắn trúng."""
        x, y = coords  # Lấy tọa độ hiện tại (vị trí đã bắn trúng)
        directions = []  # Danh sách hướng tấn công khả dĩ

        # Xác định nếu con tàu có trục dọc (North-South)
        if ((self.is_within_grid(x - 1, y) and grid[x - 1][y] == 'T') or
                (self.is_within_grid(x + 1, y) and grid[x + 1][y] == 'T')):
            directions = ['North', 'South']  # Hướng tấn công dọc
            self.moves = [(r, c) for r, c in self.moves if c == y]  # Lọc danh sách nước đi chỉ giữ lại những ô cùng cột

        # Xác định nếu con tàu có trục ngang (East-West)
        elif ((self.is_within_grid(x, y - 1) and grid[x][y - 1] == 'T') or
              (self.is_within_grid(x, y + 1) and grid[x][y + 1] == 'T')):
            directions = ['East', 'West']  # Hướng tấn công ngang
            self.moves = [(r, c) for r, c in self.moves if
                          r == x]  # Lọc danh sách nước đi chỉ giữ lại những ô cùng hàng

        # Tính toán các nước đi tiếp theo dựa trên hướng tấn công
        for direction in directions:
            nx, ny = self._get_next_position(x, y, direction)  # Lấy tọa độ của ô tiếp theo theo hướng `direction`
            if (0 <= nx < 10 and 0 <= ny < 10 and grid[nx][ny] in [' ', 'O'] and
                    (nx, ny) not in self.moves):  # Kiểm tra nếu ô hợp lệ và chưa bị chọn
                self.moves.append((nx, ny))  # Thêm vào danh sách nước đi ưu tiên

    def generate_moves(self, coords, grid):
        """Sinh các nước đi ưu tiên sau khi bắn trúng."""
        x, y = coords  # Lấy tọa độ hiện tại (vị trí đã bắn trúng)
        directions = ['North', 'South', 'East', 'West']  # Các hướng tấn công có thể thực hiện

        # Tính toán các nước đi tiếp theo cho từng hướng
        for direction in directions:
            nx, ny = self._get_next_position(x, y, direction)  # Lấy tọa độ của ô tiếp theo theo hướng `direction`

            # Kiểm tra ô hợp lệ và chưa bị chọn
            if (0 <= nx < 10 and 0 <= ny < 10 and grid[nx][ny] in [' ', 'O'] and
                    (nx, ny) not in self.moves):
                self.moves.append((nx, ny))  # Thêm vào danh sách nước đi ưu tiên

    def _get_next_position(self, x, y, direction):
        if direction == 'North':
            return x - 1, y
        elif direction == 'South':
            return x + 1, y
        elif direction == 'East':
            return x, y + 1
        elif direction == 'West':
            return x, y - 1
        return x, y  # Default, should never hit here

    def draw(self, window):
        if self.turn:
            window.blit(self.status, (cGameGrid[0][0][0] - CELLSIZE, cGameGrid[-1][-1][1] + CELLSIZE))

    def print_probability_matrix(self):
        print(np.array2string(self.probability_matrix, formatter={'float_kind': lambda x: f"{x:0.4f}"}))

# Reinforcement learning (Nhưng chưa chạy được)
class NRCOMPUTER():
    def __init__(self):
        self.turn = False
        self.status = self.computer_status('Thinking')
        self.name = 'RL Computer'
        self.q_table = {}  # Q-Table lưu trữ giá trị Q cho từng trạng thái-hành động
        self.epsilon = 0.1  # Xác suất khám phá (exploration)
        self.learning_rate = 0.1  # Hệ số học
        self.discount_factor = 0.9  # Hệ số chiết khấu (discount factor)
        self.moves = []

    def computer_status(self, msg):
        font = pygame.font.SysFont('Stencil', 22)
        return font.render(msg, 1, (0, 0, 0))

    def make_attack(self, gamelogic):
        """Máy tính thực hiện tấn công dựa trên Q-Learning."""
        state = self._encode_state(gamelogic)

        # Chọn hành động (tọa độ) dựa trên chính sách ε-greedy
        if random.uniform(0, 1) < self.epsilon:
            action = self._random_action(gamelogic)
        else:
            action = self._best_action(state, gamelogic)

        # Thực hiện hành động
        row, col = action
        reward = self._process_attack(row, col, gamelogic)

        # Cập nhật Q-Table
        next_state = self._encode_state(gamelogic)
        self._update_q_table(state, action, reward, next_state)

        return self.turn

    def _random_action(self, gamelogic):
        """Chọn ngẫu nhiên một ô hợp lệ."""
        while True:
            row, col = random.randint(0, 9), random.randint(0, 9)
            if gamelogic[row][col] in [' ', 'O']:
                return (row, col)

    def _best_action(self, state, gamelogic):
        """Chọn hành động tốt nhất dựa trên Q-Table."""
        if state not in self.q_table:
            self.q_table[state] = {}  # Khởi tạo Q-values nếu chưa có
        actions = self.q_table[state]

        # Duyệt qua các hành động hợp lệ
        best_action = None
        max_q_value = -float('inf')
        for row in range(10):
            for col in range(10):
                if gamelogic[row][col] in [' ', 'O']:  # Chỉ chọn các ô hợp lệ
                    q_value = actions.get((row, col), 0)
                    if q_value > max_q_value:
                        max_q_value = q_value
                        best_action = (row, col)
        return best_action if best_action else self._random_action(gamelogic)

    def _process_attack(self, row, col, gamelogic):
        """Thực hiện tấn công và trả về phần thưởng."""
        if gamelogic[row][col] == 'O':  # Hit
            gamelogic[row][col] = 'T'
            return 1  # Phần thưởng cho cú đánh trúng
        else:  # Miss
            gamelogic[row][col] = 'X'
            return -1  # Phần thưởng âm cho cú đánh trượt

    def _update_q_table(self, state, action, reward, next_state):
        """Cập nhật giá trị Q-Table theo công thức Q-Learning."""
        if state not in self.q_table:
            self.q_table[state] = {}
        if action not in self.q_table[state]:
            self.q_table[state][action] = 0

        # Giá trị Q hiện tại
        current_q = self.q_table[state][action]

        # Giá trị Q tối đa trong trạng thái tiếp theo
        next_max_q = max(self.q_table.get(next_state, {}).values(), default=0)

        # Cập nhật giá trị Q
        new_q = (1 - self.learning_rate) * current_q + \
                self.learning_rate * (reward + self.discount_factor * next_max_q)
        self.q_table[state][action] = new_q

    def _encode_state(self, gamelogic):
        """Mã hóa trạng thái của lưới thành chuỗi để sử dụng trong Q-Table."""
        return ''.join(''.join(row) for row in gamelogic)

    def draw(self, window):
        if self.turn:
            window.blit(self.status, (cGameGrid[0][0][0] - CELLSIZE, cGameGrid[-1][-1][1] + CELLSIZE))




#  Game Utility Functions
def createGameGrid(rows, cols, cellsize, pos):
    """Tạo danh sách tọa độ 2D cho từng ô trong lưới."""
    startX, startY = pos
    coordGrid = []
    for row in range(rows):
        rowX = []
        for col in range(cols):
            rowX.append((startX, startY))
            startX += cellsize
        coordGrid.append(rowX)
        startX = pos[0]
        startY += cellsize
    return coordGrid


def createGameLogic(rows, cols):
    """Khởi tạo lưới trò chơi với các khoảng trống (' ') cho người chơi và máy"""
    return [[' ' for _ in range(cols)] for _ in range(rows)]


def updateGameLogic(coordGrid, shiplist, gamelogic):
    for i, rowX in enumerate(coordGrid):
        for j, colX in enumerate(rowX):
            # Bỏ qua các ô đã bị tấn công hoặc phá hủy
            if gamelogic[i][j] in {'T', 'X'}:
                continue
            # Reset ô hiện tại thành trống
            gamelogic[i][j] = ' '
            # Kiểm tra va chạm với từng tàu
            cell_rect = pygame.Rect(colX[0], colX[1], CELLSIZE, CELLSIZE)
            if any(cell_rect.colliderect(ship.rect) for ship in shiplist):
                gamelogic[i][j] = 'O'  # Đánh dấu ô có tàu


def showGridOnScreen(window, cellsize, playerGrid, computerGrid):
    """Vẽ cả lưới trình phát và máy tính vào màn hình."""
    for grid in [playerGrid, computerGrid]:
        for row in grid:
            for col in row:
                pygame.draw.rect(window, (255, 255, 255), (col[0], col[1], cellsize, cellsize), 1)


def printGameLogic():
    print('Player Grid'.center(50, '#'))
    for _ in pGameLogic:
        print(_)
    print('Computer Grid'.center(50, '#'))
    for _ in cGameLogic:
        print(_)


def loadImage(path, size, rotate=False):
    """Tải hình ảnh, chia tỷ lệ và xoay hình ảnh nếu cần."""
    img = pygame.image.load(path).convert_alpha()
    img = pygame.transform.scale(img, size)
    if rotate:
        img = pygame.transform.rotate(img, -90)
    return img


def loadAnimationImages(path, aniNum,  size):
    imageList = []
    for num in range(aniNum):
        if num < 10:
            imageList.append(loadImage(f'{path}00{num}.png', size))
        elif num < 100:
            imageList.append(loadImage(f'{path}0{num}.png', size))
        else:
            imageList.append(loadImage(f'{path}{num}.png', size))
    return imageList


def loadSpriteSheetImages(spriteSheet, rows, cols, newSize, size):
    image = pygame.Surface((128, 128))
    image.blit(spriteSheet, (0, 0), (rows * size[0], cols * size[1], size[0], size[1]))
    image = pygame.transform.scale(image, (newSize[0], newSize[1]))
    image.set_colorkey((0, 0, 0))
    return image


def increaseAnimationImage(imageList, ind):
    return imageList[ind]


def createFleet():
    """Tạo ra đội tàu"""
    fleet = []
    for name in FLEET.keys():
        fleet.append(
            Ship(name,
                 FLEET[name][1],
                 FLEET[name][2],
                 FLEET[name][3],
                 FLEET[name][4],
                 FLEET[name][5],
                 FLEET[name][6],
                 FLEET[name][7])
        )
    return fleet

def sortFleet(ship, shiplist):
    """Sắp xếp lại danh sách tàu"""
    shiplist.remove(ship)
    shiplist.append(ship)


def randomizeShipPositions(shiplist, gamegrid, max_attempts=10):
    """
    Đặt ngẫu nhiên các tàu trên lưới sử dụng Random Restart Hill Climbing.
    """
    placedShips = []  # Danh sách các tàu đã đặt
    attempts = 0  # Đếm số lần khởi động lại toàn bộ

    while attempts < max_attempts:
        placedShips.clear()  # Mỗi lần khởi động lại, xóa danh sách tàu đã đặt
        validPosition = True  # Giả định ban đầu là có thể đặt tất cả các tàu

        # Lặp qua từng tàu trong danh sách
        for ship in shiplist:
            shipPlaced = False  # Trạng thái đặt tàu (chưa đặt thành công)
            retries = 0  # Số lần thử đặt lại cho từng tàu

            # Thử đặt tàu trong tối đa 'max_attempts' lần
            while not shipPlaced and retries < max_attempts:
                # Đưa tàu về vị trí mặc định (nếu có xoay trước đó)
                ship.returnToDefaultPosition()

                # Ngẫu nhiên quyết định xoay tàu (True: xoay ngang, False: giữ dọc)
                rotateShip = random.choice([True, False])
                if rotateShip:
                    # Tính tọa độ ngẫu nhiên sao cho tàu nằm gọn trên lưới
                    yAxis = random.randint(0, 9)
                    xAxis = random.randint(0, 9 - (ship.hImage.get_width() // CELLSIZE))
                    ship.rotateShip(True)  # Xoay tàu sang hướng ngang
                    ship.rect.topleft = gamegrid[yAxis][xAxis]  # Cập nhật vị trí tàu
                else:
                    # Tính tọa độ ngẫu nhiên khi tàu ở hướng dọc
                    yAxis = random.randint(0, 9 - (ship.vImage.get_height() // CELLSIZE))
                    xAxis = random.randint(0, 9)
                    ship.rect.topleft = gamegrid[yAxis][xAxis]  # Cập nhật vị trí tàu

                # Kiểm tra xem tàu có bị chồng chéo với các tàu đã đặt trước đó không
                if any(ship.rect.colliderect(item.rect) for item in placedShips):
                    retries += 1  # Nếu chồng chéo, tăng số lần thử
                else:
                    # Nếu không chồng chéo, đặt tàu thành công
                    shipPlaced = True
                    placedShips.append(ship)  # Thêm tàu vào danh sách đã đặt

            # Nếu không thể đặt tàu sau số lần thử tối đa, dừng vòng lặp và khởi động lại
            if not shipPlaced:
                validPosition = False
                break

        # Nếu tất cả các tàu được đặt thành công, trả về danh sách
        if validPosition:
            return placedShips

        # Nếu không thành công, tăng số lần khởi động lại
        attempts += 1

    # Nếu không thể đặt toàn bộ tàu sau số lần khởi động lại tối đa, báo lỗi
    raise ValueError("Không thể đặt tất cả các tàu sau số lần thử tối đa!")


def placeShipsAtFixedPositions(shiplist, gamegrid):
    """Đặt 7 con tàu vào các vị trí cố định trên lưới."""
    # Các vị trí cố định: (y, x, rotate)
    fixed_positions = [
        (1, 3, False),  # Tàu đầu tiên - tàu 4
        (2, 1, True),   # Tàu thứ hai - tàu 4
        (3, 5, False),  # Tàu thứ ba - tàu 3
        (4, 9, True),   # Tàu thứ tư - tàu 2
        (7, 7, False),  # Tàu thứ năm - tàu 3
        (8, 2, False),   # Tàu thứ sáu - tàu 5
        (6, 4, False)   # Tàu thứ bảy - tàu 2
    ]

    # Đảm bảo danh sách có đúng 7 tàu
    if len(shiplist) != 7:
        raise ValueError("Số lượng tàu không đúng, cần 7 tàu!")

    # Đảm bảo số vị trí cố định bằng số tàu
    if len(fixed_positions) != len(shiplist):
        raise ValueError("Số lượng vị trí cố định không khớp với số lượng tàu!")

    placed_ships = []  # Danh sách tàu đã đặt thành công

    for ship, (y, x, rotate) in zip(shiplist, fixed_positions):
        ship.returnToDefaultPosition()  # Đưa tàu về vị trí mặc định
        if rotate:  # Nếu cần xoay ngang
            ship.rotateShip(True)

        # Kiểm tra xem tọa độ có hợp lệ trên lưới không
        if y >= len(gamegrid[1]) or x >= len(gamegrid[0]):
            raise ValueError(f"Tọa độ ({y}, {x}) vượt quá kích thước lưới!")

        # Đặt vị trí cố định cho tàu
        ship.rect.topleft = gamegrid[x][y]
        placed_ships.append(ship)  # Lưu lại tàu đã đặt

    # Kiểm tra kết quả sau khi đặt
    if len(placed_ships) != len(shiplist):
        raise RuntimeError("Không phải tất cả các tàu đều được đặt thành công!")

    return placed_ships


def placeShipsAtSeamlessFixedPositions(shiplist, gamegrid):
    """Đặt 7 con tàu vào các vị trí cố định trên lưới."""
    # Các vị trí cố định: (y, x, rotate)
    fixed_positions = [
        (2, 2, False),  # Tàu đầu tiên - tàu 4
        (2, 1, True),   # Tàu thứ hai - tàu 4
        (3, 5, False),  # Tàu thứ ba - tàu 3
        (4, 7, True),   # Tàu thứ tư - tàu 2
        (6, 6, False),  # Tàu thứ năm - tàu 3
        (4, 3, True),   # Tàu thứ sáu - tàu 5
        (6, 4, False)   # Tàu thứ bảy - tàu 2
    ]

    # Đảm bảo danh sách có đúng 7 tàu
    if len(shiplist) != 7:
        raise ValueError("Số lượng tàu không đúng, cần 7 tàu!")

    # Đảm bảo số vị trí cố định bằng số tàu
    if len(fixed_positions) != len(shiplist):
        raise ValueError("Số lượng vị trí cố định không khớp với số lượng tàu!")

    placed_ships = []  # Danh sách tàu đã đặt thành công

    for ship, (y, x, rotate) in zip(shiplist, fixed_positions):
        ship.returnToDefaultPosition()  # Đưa tàu về vị trí mặc định
        if rotate:  # Nếu cần xoay ngang
            ship.rotateShip(True)

        # Kiểm tra xem tọa độ có hợp lệ trên lưới không
        if y >= len(gamegrid[1]) or x >= len(gamegrid[0]):
            raise ValueError(f"Tọa độ ({y}, {x}) vượt quá kích thước lưới!")

        # Đặt vị trí cố định cho tàu
        ship.rect.topleft = gamegrid[x][y]
        placed_ships.append(ship)  # Lưu lại tàu đã đặt

    # Kiểm tra kết quả sau khi đặt
    if len(placed_ships) != len(shiplist):
        raise RuntimeError("Không phải tất cả các tàu đều được đặt thành công!")

    return placed_ships

def deploymentPhase(deployment):
    if deployment == True:
        return False
    else:
        return True

def pick_random_ship_location(gameLogic):
    """Chọn một vị trí hợp lệ ngẫu nhiên cho một con tàu."""
    validChoice = False
    while not validChoice:
        posX = random.randint(0, 9)
        posY = random.randint(0, 9)
        if gameLogic[posX][posY] == ' ':
            validChoice = True
    return (posX, posY)


def displayRadarScanner(imagelist, indnum, SCANNER):
    if SCANNER == True and indnum <= 359:
        image = increaseAnimationImage(imagelist, indnum)
        return image
    else:
        return False


def displayRadarBlip(num, position):
    if SCANNER:
        image = None
        if position[0] >= 5 and position[1] >= 5:
            if num >= 0 and num <= 90:
                image = increaseAnimationImage(RADARBLIPIMAGES, num // 10)
        elif position[0] < 5 and position[1] >= 5:
            if num > 270 and num <= 360:
                image = increaseAnimationImage(RADARBLIPIMAGES, (num // 4) // 10)
        elif position[0] < 5 and position[1] < 5:
            if num > 180 and num <= 270:
                image = increaseAnimationImage(RADARBLIPIMAGES, (num // 3) // 10)
        elif position[0] >= 5 and position[1] < 5:
            if num > 90 and num <= 180:
                image = increaseAnimationImage(RADARBLIPIMAGES, (num // 2) // 10)
        return image


def takeTurns(p1, p2):
    """Lượt luân phiên giữa những người chơi."""
    if p1.turn:
        p2.turn = False
    else:
        p2.turn = True
        if not p2.make_attack(pGameLogic):
            p1.turn = True


def checkForWinners(grid):
    validGame = True
    for row in grid:
        if 'O' in row:
            validGame = False
    return validGame


def shipLabelMaker(msg):
    """Tạo tên tàu và xoay dọc"""
    font = pygame.font.SysFont('Stencil', 22)
    textMessage = font.render(msg, 1, (255, 200, 15))
    return pygame.transform.rotate(textMessage, 90)


def displayShipNames(window):
    """In tên tàu lên cạnh tàu"""
    shipLabels = []
    for ship in ['carrier', 'battleship', 'cruiser', 'destroyer', 'submarine', 'patrol boat', 'rescue boat']:
        shipLabels.append(shipLabelMaker(ship))
    startPos = 25
    for item in shipLabels:
        window.blit(item, (startPos, 600))
        startPos += 75


def mainMenuScreen(window):
    window.fill((0, 0, 0))
    window.blit(MAINMENUIMAGE, (0, 0))
    window.blit(TITLEIMAGE, (-15, -90))
    window.blit(NAME1IMAGE, (500, 5))

    for button in BUTTONS:
        if button.name in ['DFS', 'BackTracking', 'Adversarial', 'Greedy', 'NeuralNetwork','Optimal', 'Instructions']:
            button.active = True
            button.draw(window)
        else:
            button.active = False
    
        MENUSOUND.play()



def deploymentScreen(window):
    MENUSOUND.stop()
    WINSOUND.stop()
    LOSESOUND.stop()


    window.fill((0, 0, 0))
    
    window.blit(BACKGROUND, (0, 0))
    window.blit(PGAMEGRIDIMG, (0, 0))
    window.blit(CGAMEGRIDIMG, (cGameGrid[0][0][0] - 50, cGameGrid[0][0][1] - 50))
    window.blit(NAME1IMAGE, (950, 750))

    #  Draws the player and computer grids to the screen
    # showGridOnScreen(window, CELLSIZE, pGameGrid, cGameGrid)

    #  Draw ships to screen
    for ship in pFleet:
        ship.draw(window)
        ship.snapToGridEdge(pGameGrid)
        ship.snapToGrid(pGameGrid)

    displayShipNames(window)

    for ship in cFleet:
        ship.snapToGridEdge(cGameGrid)
        ship.snapToGrid(cGameGrid)

    for button in BUTTONS:
        if button.name in ['Randomize','SparseFix','SeamlessFix', 'Reset', 'Start', 'Quit', 'Radar Scan', 'Redeploy']:
            button.active = True
            button.draw(window)
        else:
            button.active = False

    computer.draw(window)

    radarScan = displayRadarScanner(RADARGRIDIMAGES, INDNUM, SCANNER)
    if not radarScan:
        pass
    else:
        window.blit(radarScan, (cGameGrid[0][0][0], cGameGrid[0][0][1]))
        window.blit(RADARGRID, (cGameGrid[0][0][0], cGameGrid[0][0][1]))

    RBlip = displayRadarBlip(INDNUM, BLIPPOSITION)
    if RBlip:
        window.blit(RBlip, (cGameGrid[BLIPPOSITION[0]][BLIPPOSITION[1]][0],
                            cGameGrid[BLIPPOSITION[0]][BLIPPOSITION[1]][1]))

    for token in TOKENS:
        token.draw(window)

    updateGameLogic(pGameGrid, pFleet, pGameLogic)
    updateGameLogic(cGameGrid, cFleet, cGameLogic)


def endScreen(window, win):
    window.fill((0, 0, 0))

    if win:
        window.blit(WINSCREENIMAGE, (0, 0))
        window.blit(WINIMAGE, (0, -220))
        WINSOUND.play()
    else: 
        window.blit(LOSESCREENIMAGE, (0, 0))
        window.blit(LOSEIMAGE, (0, -220))
        LOSESOUND.play()

    window.blit(NAME1IMAGE, (500, 5))
    for button in BUTTONS:
        if button.name in ['DFS', 'BackTracking', 'Adversarial', 'Greedy', 'NeuralNetwork', 'Optimal']:
            button.active = True
            button.draw(window)
        else:
            button.active = False


def updateGameScreen(window, GAMESTATE, win):
    """Cập nhật màn hình trò chơi dựa trên trạng thái trò chơi hiện tại."""
    if GAMESTATE == 'Main Menu':
        mainMenuScreen(window)
    elif GAMESTATE == 'Deployment':
        deploymentScreen(window)
    elif GAMESTATE == 'Game Over':
        endScreen(window, win)
    pygame.display.update()


#  Game Settings and Variables
SCREENWIDTH = 1260
SCREENHEIGHT = 800
ROWS = 10
COLS = 10
CELLSIZE = 50
DEPLOYMENT = True
SCANNER = False
INDNUM = 0
BLIPPOSITION = None
TURNTIMER = pygame.time.get_ticks()
GAMESTATE = 'Main Menu'


#  Pygame Display Initialization
GAMESCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
pygame.display.set_caption('Battle Ship')


#  Game Lists/Dictionaries
FLEET = {
    'battleship': ['battleship', 'assets/images/ships/battleship/battleship.png', (125, 560), (40, 195),
                   4, 'assets/images/ships/battleship/battleshipgun.png', (0.4, 0.125), [-0.525, -0.34, 0.67, 0.49]],
    'cruiser': ['cruiser', 'assets/images/ships/cruiser/cruiser.png', (200, 560), (40, 195),
                2, 'assets/images/ships/cruiser/cruisergun.png', (0.4, 0.125), [-0.36, 0.64]],
    'destroyer': ['destroyer', 'assets/images/ships/destroyer/destroyer.png', (275, 580), (30, 145),
                  2, 'assets/images/ships/destroyer/destroyergun.png', (0.5, 0.15), [-0.52, 0.71]],
    'patrol boat': ['patrol boat', 'assets/images/ships/patrol boat/patrol boat.png', (425, 600), (20, 95),
                    0, '', None, None],
    'submarine': ['submarine', 'assets/images/ships/submarine/submarine.png', (350, 590), (30, 145),
                  1, 'assets/images/ships/submarine/submarinegun.png', (0.25, 0.125), [-0.45]],
    'carrier': ['carrier', 'assets/images/ships/carrier/carrier.png', (50, 555), (45, 245),
                0, '', None, None],
    'rescue ship': ['rescue ship', 'assets/images/ships/rescue ship/rescue ship.png', (500, 600), (20, 95),
                    0, '', None, None]
}
STAGE = ['Main Menu', 'Deployment', 'Game Over']

#  Loading Game Variables
pGameGrid = createGameGrid(ROWS, COLS, CELLSIZE, (50, 50))
pGameLogic = createGameLogic(ROWS, COLS)
pFleet = createFleet()

cGameGrid = createGameGrid(ROWS, COLS, CELLSIZE, (SCREENWIDTH - (ROWS * CELLSIZE), 50))
cGameLogic = createGameLogic(ROWS, COLS)
cFleet = createFleet()
randomizeShipPositions(cFleet, cGameGrid)

printGameLogic()

#  Loading Game Sounds and Images
MAINMENUIMAGE = loadImage('assets/images/background/battleshipmenu2.jpg', (SCREENWIDTH, SCREENHEIGHT))
TITLEIMAGE = loadImage('assets/images/background/title2.png', (SCREENWIDTH, SCREENHEIGHT))
INSIMAGE = loadImage('assets/images/background/instruction.png', (SCREENWIDTH, SCREENHEIGHT))
NAMEIMAGE = loadImage('assets/images/background/NAME.png', (270, 70))
NAME1IMAGE = loadImage('assets/images/background/NAME1.png', (270, 20))
LOSEIMAGE = loadImage('assets/images/background/youlose.png', (SCREENWIDTH, SCREENHEIGHT))
WINIMAGE = loadImage('assets/images/background/youwin.png', (SCREENWIDTH, SCREENHEIGHT))
LOSESCREENIMAGE = loadImage('assets/images/background/newlose.png', (SCREENWIDTH, SCREENHEIGHT))
WINSCREENIMAGE = loadImage('assets/images/background/newwin.png', (SCREENWIDTH, SCREENHEIGHT))
BACKGROUND = loadImage('assets/images/background/bgongame4.png', (SCREENWIDTH, SCREENHEIGHT))
PGAMEGRIDIMG = loadImage('assets/images/grids/NEWgrid.png', ((ROWS + 1) * CELLSIZE, (COLS + 1) * CELLSIZE))
CGAMEGRIDIMG = loadImage('assets/images/grids/comp_grid.png', ((ROWS + 1) * CELLSIZE, (COLS + 1) * CELLSIZE))
BUTTONIMAGE = loadImage('assets/images/buttons/newbutton.png', (150, 50))
BUTTONIMAGE1 = loadImage('assets/images/buttons/buttonvip.png', (250, 100))
BUTTONS = [
    Button(BUTTONIMAGE, (150, 50), (725, 600), 'Randomize'),
    Button(BUTTONIMAGE, (150, 50), (725, 680), 'SparseFix'),
    Button(BUTTONIMAGE, (150, 50), (900, 680), 'SeamlessFix'),
    Button(BUTTONIMAGE, (150, 50), (900, 600), 'Reset'),
    Button(BUTTONIMAGE, (150, 50), (1075, 600), 'Start'),
    Button(BUTTONIMAGE1, (250, 100), (170, SCREENHEIGHT // 2 + 160), 'DFS'),
    Button(BUTTONIMAGE1, (250, 100), (500, SCREENHEIGHT // 2 + 160), 'BackTracking'),
    Button(BUTTONIMAGE1, (250, 100), (830, SCREENHEIGHT // 2 + 160), 'Adversarial'),
    Button(BUTTONIMAGE1, (250, 100), (170, SCREENHEIGHT // 2 + 275), 'Greedy'),
    Button(BUTTONIMAGE1, (250, 100), (500, SCREENHEIGHT // 2 + 275), 'NeuralNetwork'),
    Button(BUTTONIMAGE1, (250, 100), (830, SCREENHEIGHT // 2 + 275), 'Optimal'),
]
REDTOKEN = loadImage('assets/images/tokens/BanTrung.png', (CELLSIZE, CELLSIZE))
GREENTOKEN = loadImage('assets/images/tokens/BanHut.png', (CELLSIZE, CELLSIZE))
BLUETOKEN = loadImage('assets/images/tokens/Hut2.png', (CELLSIZE, CELLSIZE))
FIRETOKENIMAGELIST = loadAnimationImages('assets/images/tokens/fireloop/fire1_ ', 13, (CELLSIZE, CELLSIZE))
EXPLOSIONSPRITESHEET = pygame.image.load('assets/images/tokens/explosion/explosion.png').convert_alpha()
EXPLOSIONIMAGELIST = []
for row in range(8):
    for col in range(8):
        EXPLOSIONIMAGELIST.append(loadSpriteSheetImages(EXPLOSIONSPRITESHEET, col, row, (CELLSIZE, CELLSIZE), (128, 128)))
TOKENS = []
RADARGRIDIMAGES = loadAnimationImages('assets/images/radar_base/radar_anim', 360, (ROWS * CELLSIZE, COLS * CELLSIZE))
RADARBLIPIMAGES = loadAnimationImages('assets/images/radar_blip/Blip_', 11, (50, 50))
RADARGRID = loadImage('assets/images/grids/grid_faint.png', ((ROWS) * CELLSIZE, (COLS) * CELLSIZE))
HITSOUND = pygame.mixer.Sound('assets/sounds/explosion.wav')
HITSOUND.set_volume(0.05)
SHOTSOUND = pygame.mixer.Sound('assets/sounds/gunshot.wav')
SHOTSOUND.set_volume(0.05)
MISSSOUND = pygame.mixer.Sound('assets/sounds/splash.wav')
MISSSOUND.set_volume(0.05)
MENUSOUND = pygame.mixer.Sound('assets/sounds/menu.mp3')
MENUSOUND.set_volume(0.1)
LOSESOUND = pygame.mixer.Sound('assets/sounds/lose.mp3')
LOSESOUND.set_volume(0.1)
WINSOUND = pygame.mixer.Sound('assets/sounds/victory.mp3')
WINSOUND.set_volume(0.1)


#  Initialise Players
player1 = Player()
computer = DFSCOMPUTER()

p1win = True
# Vòng lặp chính để chạy game
while True:
    # Xử lý các sự kiện trong hàng đợi sự kiện của pygame
    for event in pygame.event.get():
        # Nếu sự kiện là đóng cửa sổ (QUIT), thoát chương trình
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Nếu sự kiện là nhấn chuột
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Chuột trái
                if DEPLOYMENT:  # Trong giai đoạn triển khai
                    for ship in pFleet:  # Kiểm tra tất cả các tàu trong đội tàu của người chơi
                        if ship.rect.collidepoint(pygame.mouse.get_pos()):  # Nếu chuột nằm trên một tàu
                            ship.active = True  # Đặt tàu này thành hoạt động
                            sortFleet(ship, pFleet)  # Sắp xếp lại đội tàu
                            ship.selectShipAndMove()  # Kích hoạt chế độ chọn và di chuyển tàu
                else:  # Nếu không phải giai đoạn triển khai
                    if player1.turn:  # Kiểm tra lượt chơi của người chơi 1
                        player1.make_attack(cGameGrid, cGameLogic)  # Người chơi 1 tấn công
                        if not player1.turn:  # Nếu lượt chuyển sang máy tính
                            TURNTIMER = pygame.time.get_ticks()  # Đặt thời gian bắt đầu lượt máy tính

                # Xử lý khi nhấn vào các nút giao diện
                for button in BUTTONS:
                    if button.rect.collidepoint(pygame.mouse.get_pos()):  # Nếu chuột nhấn lên nút
                        if button.name == 'Start' and button.active:
                            DEPLOYMENT = deploymentPhase(DEPLOYMENT)  # Bắt đầu giai đoạn triển khai
                        elif button.name == 'Redeploy' and button.active:
                            DEPLOYMENT = deploymentPhase(DEPLOYMENT)  # Triển khai lại đội hình
                        elif button.name == 'Quit' and button.active:
                            pygame.quit()  # Thoát game
                            sys.exit()
                        elif button.name == 'Radar Scan' and button.active:
                            SCANNER = True  # Bật chế độ quét radar
                            INDNUM = 0  # Khởi tạo số đếm chỉ số radar
                            BLIPPOSITION = pick_random_ship_location(cGameLogic)  # Chọn vị trí ngẫu nhiên để quét
                        # Xử lý các chế độ chơi máy tính khác nhau
                        elif (button.name == 'DFS' or button.name == 'BackTracking' or
                              button.name == 'Adversarial' or button.name == 'Greedy' or
                              button.name == 'NeuralNetwork'or
                              button.name == 'Optimal' or button.name == 'Instructions' ) and button.active:
                            # Khởi tạo máy tính phù hợp với chế độ được chọn
                            if button.name == 'DFS':
                                computer = DFSCOMPUTER()
                            elif button.name == 'BackTracking':
                                computer = BTCOMPUTER()
                            elif button.name == 'Adversarial':
                                computer = ADVCOMPUTER()
                            elif button.name == 'Greedy':
                                computer = GCOMPUTER()
                            elif button.name == 'NeuralNetwork':
                                computer = NRCOMPUTER()
                            elif button.name == 'Optimal':
                                computer = OPTIMALMODE()
                            # Nếu trạng thái trò chơi kết thúc, thiết lập lại trò chơi
                            if GAMESTATE == 'Game Over':
                                TOKENS.clear()
                                for ship in pFleet:
                                    ship.returnToDefaultPosition()
                                randomizeShipPositions(cFleet, cGameGrid)
                                pGameLogic = createGameLogic(ROWS, COLS)
                                updateGameLogic(pGameGrid, pFleet, pGameLogic)
                                cGameLogic = createGameLogic(ROWS, COLS)
                                updateGameLogic(cGameGrid, cFleet, cGameLogic)
                                DEPLOYMENT = deploymentPhase(DEPLOYMENT)
                            GAMESTATE = STAGE[1]  # Cập nhật trạng thái trò chơi
                        button.handle_action()  # Thực hiện hành động của nút

            elif event.button == 2:  # Chuột giữa
                printGameLogic()  # In logic trò chơi ra console để kiểm tra

            elif event.button == 3:  # Chuột phải
                if DEPLOYMENT:  # Trong giai đoạn triển khai
                    for ship in pFleet:
                        if ship.rect.collidepoint(pygame.mouse.get_pos()):  # Nếu chuột nằm trên một tàu
                            if not ship.checkForRotateCollisions(pFleet):  # Nếu không có va chạm khi xoay
                                ship.rotateShip(True)  # Xoay tàu

    # Cập nhật giao diện màn hình trò chơi
    updateGameScreen(GAMESCREEN, GAMESTATE, p1win)

    if SCANNER:  # Nếu đang ở chế độ quét radar
        INDNUM += 1  # Tăng chỉ số radar

    # Kiểm tra các trạng thái trò chơi để chuyển đổi
    if GAMESTATE == 'Deployment' and not DEPLOYMENT:  # Nếu hoàn tất triển khai
        player1Wins = checkForWinners(cGameLogic)  # Kiểm tra người chơi 1 chiến thắng
        computerWins = checkForWinners(pGameLogic)  # Kiểm tra máy tính chiến thắng
        if player1Wins:
            GAMESTATE = STAGE[2]  # Cập nhật trạng thái thành người chơi chiến thắng
        elif computerWins:
            p1win = False
            GAMESTATE = STAGE[2]  # Cập nhật trạng thái thành máy tính chiến thắng

    # Thực hiện lượt chơi luân phiên giữa người chơi và máy tính
    takeTurns(player1, computer)
