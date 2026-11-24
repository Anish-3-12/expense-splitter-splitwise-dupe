package com.example.expensesplitter.controller;

import com.example.expensesplitter.dto.CategoryDto;
import com.example.expensesplitter.repository.ExpenseCategoryRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/categories")
public class CategoryController {

    private final ExpenseCategoryRepository categoryRepository;

    public CategoryController(ExpenseCategoryRepository categoryRepository) {
        this.categoryRepository = categoryRepository;
    }

    @GetMapping
    public ResponseEntity<List<CategoryDto>> listCategories() {
        List<CategoryDto> list = categoryRepository.findAll().stream()
                .map(c -> new CategoryDto(c.getId(), c.getName(), c.getIcon(), c.getDescription()))
                .collect(Collectors.toList());
        return ResponseEntity.ok(list);
    }
}
