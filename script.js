document.addEventListener('DOMContentLoaded', () => {
    const mainMenu = document.getElementById('main-menu');
    const gameScreen = document.getElementById('game-screen');
    const gameOverModal = document.getElementById('game-over-modal');
    
    const startBtn = document.getElementById('start-btn');
    const backBtn = document.getElementById('back-btn');
    const restartBtn = document.getElementById('restart-btn');
    const menuBtn = document.getElementById('menu-btn');
    
    const currentScoreEl = document.getElementById('current-score');
    const highScoreEl = document.getElementById('high-score');
    const finalScoreEl = document.getElementById('final-score');
    const previewScoreEl = document.getElementById('preview-score');
    
    const canvas = document.getElementById('game-canvas');
    const ctx = canvas.getContext('2d');
    const previewCanvas = document.getElementById('preview-canvas');
    const previewCtx = previewCanvas.getContext('2d');
    
    // Game variables
    const gridSize = 20;
    const tileCount = canvas.width / gridSize;
    let snake = [];
    let food = {};
    let dx = 0;
    let dy = -1;
    let score = 0;
    let highScore = localStorage.getItem('snakeHighScore') || 0;
    let gameLoop;
    let speed = 100;
    let isGameOver = false;

    highScoreEl.textContent = highScore;

    // Load recent game preview if exists
    loadRecentPreview();

    // Event Listeners
    startBtn.addEventListener('click', startGame);
    backBtn.addEventListener('click', showMenu);
    restartBtn.addEventListener('click', startGame);
    menuBtn.addEventListener('click', showMenu);
    document.addEventListener('keydown', handleKeyPress);

    function showMenu() {
        gameScreen.classList.add('hidden');
        gameOverModal.classList.add('hidden');
        mainMenu.classList.remove('hidden');
        loadRecentPreview();
        clearInterval(gameLoop);
    }

    function startGame() {
        mainMenu.classList.add('hidden');
        gameOverModal.classList.add('hidden');
        gameScreen.classList.remove('hidden');
        
        // Reset game state
        snake = [
            { x: Math.floor(tileCount/2), y: Math.floor(tileCount/2) },
            { x: Math.floor(tileCount/2), y: Math.floor(tileCount/2) + 1 },
            { x: Math.floor(tileCount/2), y: Math.floor(tileCount/2) + 2 }
        ];
        dx = 0;
        dy = -1;
        score = 0;
        isGameOver = false;
        speed = 120;
        currentScoreEl.textContent = score;
        
        spawnFood();
        
        if (gameLoop) clearInterval(gameLoop);
        gameLoop = setInterval(update, speed);
    }

    function handleKeyPress(e) {
        if (isGameOver) return;
        
        // Prevent default scrolling for arrow keys
        if([37, 38, 39, 40].indexOf(e.keyCode) > -1) {
            e.preventDefault();
        }

        const KEY_UP = 38;
        const KEY_DOWN = 40;
        const KEY_LEFT = 37;
        const KEY_RIGHT = 39;
        const W = 87;
        const S = 83;
        const A = 65;
        const D = 68;

        const goingUp = dy === -1;
        const goingDown = dy === 1;
        const goingRight = dx === 1;
        const goingLeft = dx === -1;

        if ((e.keyCode === KEY_LEFT || e.keyCode === A) && !goingRight) {
            dx = -1; dy = 0;
        } else if ((e.keyCode === KEY_UP || e.keyCode === W) && !goingDown) {
            dx = 0; dy = -1;
        } else if ((e.keyCode === KEY_RIGHT || e.keyCode === D) && !goingLeft) {
            dx = 1; dy = 0;
        } else if ((e.keyCode === KEY_DOWN || e.keyCode === S) && !goingUp) {
            dx = 0; dy = 1;
        }
    }

    function spawnFood() {
        food = {
            x: Math.floor(Math.random() * tileCount),
            y: Math.floor(Math.random() * tileCount)
        };
        // Ensure food doesn't spawn on snake
        for (let segment of snake) {
            if (segment.x === food.x && segment.y === food.y) {
                spawnFood();
                return;
            }
        }
    }

    function update() {
        // Move snake
        const head = { x: snake[0].x + dx, y: snake[0].y + dy };
        
        // Check collisions (walls)
        if (head.x < 0 || head.x >= tileCount || head.y < 0 || head.y >= tileCount) {
            gameOver();
            return;
        }

        // Check collisions (self)
        for (let i = 0; i < snake.length; i++) {
            if (head.x === snake[i].x && head.y === snake[i].y) {
                gameOver();
                return;
            }
        }

        snake.unshift(head);

        // Check food collection
        if (head.x === food.x && head.y === food.y) {
            score += 10;
            currentScoreEl.textContent = score;
            if (score > highScore) {
                highScore = score;
                highScoreEl.textContent = highScore;
                localStorage.setItem('snakeHighScore', highScore);
            }
            // Increase speed slightly
            if (speed > 50) {
                speed -= 2;
                clearInterval(gameLoop);
                gameLoop = setInterval(update, speed);
            }
            spawnFood();
        } else {
            snake.pop();
        }

        draw(ctx, canvas.width, canvas.height, gridSize);
    }

    function draw(context, w, h, gSize) {
        // Clear canvas
        context.clearRect(0, 0, w, h);

        // Draw grid
        context.strokeStyle = 'rgba(255, 255, 255, 0.05)';
        context.lineWidth = 1;
        for(let i=0; i<=w; i+=gSize) {
            context.beginPath();
            context.moveTo(i, 0);
            context.lineTo(i, h);
            context.stroke();
            context.beginPath();
            context.moveTo(0, i);
            context.lineTo(w, i);
            context.stroke();
        }

        // Draw food
        const fSize = gSize - 2;
        context.fillStyle = '#f43f5e';
        context.shadowColor = '#f43f5e';
        context.shadowBlur = 15;
        context.beginPath();
        context.arc(food.x * gSize + gSize/2, food.y * gSize + gSize/2, fSize/2, 0, Math.PI * 2);
        context.fill();
        context.shadowBlur = 0;

        // Draw snake
        snake.forEach((segment, index) => {
            context.fillStyle = index === 0 ? '#22d3ee' : '#4ade80';
            context.shadowColor = index === 0 ? '#22d3ee' : '#4ade80';
            context.shadowBlur = index === 0 ? 10 : 5;
            
            context.fillRect(segment.x * gSize + 1, segment.y * gSize + 1, gSize - 2, gSize - 2);
        });
        context.shadowBlur = 0;
    }

    function gameOver() {
        isGameOver = true;
        clearInterval(gameLoop);
        
        // Save recent game snapshot
        saveRecentGame();
        
        finalScoreEl.textContent = score;
        setTimeout(() => {
            gameOverModal.classList.remove('hidden');
        }, 500);
    }

    function saveRecentGame() {
        const state = {
            snake: JSON.parse(JSON.stringify(snake)),
            food: { ...food },
            score: score
        };
        localStorage.setItem('recentGameState', JSON.stringify(state));
    }

    function loadRecentPreview() {
        const saved = localStorage.getItem('recentGameState');
        if (saved) {
            try {
                const state = JSON.parse(saved);
                previewScoreEl.textContent = `Score: ${state.score}`;
                
                // Draw to preview canvas
                const pGridSize = 10; // Half size since preview canvas is 200x200 vs 400x400
                
                // Clear
                previewCtx.clearRect(0, 0, previewCanvas.width, previewCanvas.height);
                
                // Draw food
                previewCtx.fillStyle = '#f43f5e';
                previewCtx.beginPath();
                previewCtx.arc(state.food.x * pGridSize + pGridSize/2, state.food.y * pGridSize + pGridSize/2, (pGridSize-2)/2, 0, Math.PI * 2);
                previewCtx.fill();
                
                // Draw snake
                state.snake.forEach((segment, index) => {
                    previewCtx.fillStyle = index === 0 ? '#22d3ee' : '#4ade80';
                    previewCtx.fillRect(segment.x * pGridSize + 1, segment.y * pGridSize + 1, pGridSize - 2, pGridSize - 2);
                });
                
            } catch(e) {
                console.error('Error loading preview', e);
            }
        }
    }
});
