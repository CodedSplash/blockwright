package main

import (
	"bufio"
	"fmt"
	"os"
)

type Stack struct{ items []int }

func (s *Stack) Push(v int) { s.items = append(s.items, v) }

func (s *Stack) Pop() (int, bool) {
	if len(s.items) == 0 {
		return 0, false
	}
	v := s.items[len(s.items)-1]
	s.items = s.items[:len(s.items)-1]
	return v, true
}

func fib(n int) int {
	a, b := 0, 1
	for i := 0; i < n; i++ {
		a, b = b, a+b
	}
	return a
}

func main() {
	var n int
	fmt.Print("n = ")
	fmt.Scan(&n)
	reader := bufio.NewReader(os.Stdin)
	name, _ := reader.ReadString('\n')
	fmt.Printf("Привет, %s! fib(%d) = %d\n", name, n, fib(n))
	s := &Stack{}
	for i := range 5 {
		s.Push(i)
	}
	for {
		v, ok := s.Pop()
		if !ok {
			break
		}
		fmt.Println("pop", v)
	}
	switch {
	case n < 0:
		fmt.Println("отрицательное")
	case n == 0:
		fmt.Println("ноль")
	default:
		fmt.Println("положительное")
	}
	switch n % 3 {
	case 0:
		fmt.Println("0")
		fallthrough
	case 1:
		fmt.Println("0 или 1")
	}
	for n > 10 {
		n /= 2
	}
}
