{ Тот же пример, что grades.cpp, но на Pascal: тело программы
  становится схемой «Начало … Конец», for … to — блоком «подготовка».

      python -m blockwright examples/pascal --open }

program Grades;

const
  MaxStudents = 30;

var
  scores: array[1..MaxStudents] of integer;
  count, i, best: integer;

function Verdict(score: integer): string;
begin
  case score div 10 of
    9, 10: Verdict := 'отлично';
    7, 8: Verdict := 'хорошо';
    5, 6: Verdict := 'удовлетворительно';
  else
    Verdict := 'неудовлетворительно';
  end;
end;

function Average(n: integer): real;
var
  k, sum: integer;
begin
  sum := 0;
  for k := 1 to n do
    sum := sum + scores[k];
  Average := sum / n;
end;

begin
  write('Сколько студентов в группе? ');
  readln(count);
  if (count < 1) or (count > MaxStudents) then
  begin
    writeln('Допустимо от 1 до ', MaxStudents, ' студентов');
    halt;
  end;

  for i := 1 to count do
  begin
    write('Балл студента #', i, ': ');
    readln(scores[i]);
    if (scores[i] < 0) or (scores[i] > 100) then
    begin
      writeln('Балл вне диапазона 0..100, засчитан как 0');
      scores[i] := 0;
    end;
  end;

  best := 1;
  for i := 2 to count do
    if scores[i] > scores[best] then
      best := i;

  writeln('Средний балл: ', Average(count):0:1);
  writeln('Лучший результат: ', scores[best], ' (', Verdict(scores[best]), ')');
end.
